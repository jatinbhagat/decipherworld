"""
Monitoring and logging utilities for simplified Design Thinking sessions
Provides comprehensive logging, performance tracking, and error monitoring
"""

import logging
import time
import json
from datetime import datetime, timedelta
from functools import wraps
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from typing import Dict, Any, Optional

# Configure group learning logger
logger = logging.getLogger('group_learning')


class PerformanceMonitor:
    """Monitor performance metrics for simplified Design Thinking sessions"""
    
    def __init__(self):
        self.metrics_cache_timeout = 300  # 5 minutes
    
    def track_operation(self, operation_name: str):
        """Decorator to track operation performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                operation_id = f"{operation_name}_{int(start_time)}"
                
                try:
                    logger.info(f"🚀 Starting {operation_name} (ID: {operation_id})")
                    result = func(*args, **kwargs)
                    
                    duration = time.time() - start_time
                    self._log_success(operation_name, duration, operation_id)
                    self._update_metrics(operation_name, duration, True)
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    self._log_error(operation_name, duration, operation_id, str(e))
                    self._update_metrics(operation_name, duration, False)
                    raise
                    
            return wrapper
        return decorator
    
    def _log_success(self, operation: str, duration: float, operation_id: str):
        """Log successful operation"""
        if duration > 5.0:  # Slow operation threshold
            logger.warning(f"⚠️ SLOW {operation} completed in {duration:.2f}s (ID: {operation_id})")
        elif duration > 1.0:
            logger.info(f"✅ {operation} completed in {duration:.2f}s (ID: {operation_id})")
        else:
            logger.debug(f"✅ {operation} completed in {duration:.3f}s (ID: {operation_id})")
    
    def _log_error(self, operation: str, duration: float, operation_id: str, error: str):
        """Log failed operation"""
        logger.error(f"❌ {operation} FAILED after {duration:.2f}s (ID: {operation_id}): {error}")
    
    def _update_metrics(self, operation: str, duration: float, success: bool):
        """Update cached performance metrics"""
        try:
            cache_key = f"perf_metrics_{operation}"
            metrics = cache.get(cache_key, {
                'total_calls': 0,
                'total_duration': 0.0,
                'success_count': 0,
                'error_count': 0,
                'avg_duration': 0.0,
                'last_updated': timezone.now().isoformat()
            })
            
            metrics['total_calls'] += 1
            metrics['total_duration'] += duration
            
            if success:
                metrics['success_count'] += 1
            else:
                metrics['error_count'] += 1
            
            metrics['avg_duration'] = metrics['total_duration'] / metrics['total_calls']
            metrics['last_updated'] = timezone.now().isoformat()
            
            cache.set(cache_key, metrics, self.metrics_cache_timeout)
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")
    
    def get_operation_metrics(self, operation: str) -> Dict[str, Any]:
        """Get performance metrics for specific operation"""
        cache_key = f"perf_metrics_{operation}"
        return cache.get(cache_key, {})
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all cached performance metrics"""
        try:
            # Common operations to check
            operations = [
                'process_phase_input',
                'save_teacher_score', 
                'check_auto_progression',
                'broadcast_input_update',
                'validate_input_data',
                'update_completion_tracking'
            ]
            
            all_metrics = {}
            for operation in operations:
                metrics = self.get_operation_metrics(operation)
                if metrics:
                    all_metrics[operation] = metrics
            
            # Add database metrics
            all_metrics['database'] = self._get_database_metrics()
            
            return all_metrics
            
        except Exception as e:
            logger.error(f"Error getting all metrics: {str(e)}")
            return {}
    
    def _get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            # Get query count from Django connection
            query_count = len(connection.queries) if hasattr(connection, 'queries') else 0
            
            return {
                'query_count': query_count,
                'queries_enabled': getattr(settings, 'DEBUG', False),
                'last_updated': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting database metrics: {str(e)}")
            return {}


class SessionActivityMonitor:
    """Monitor activity and health of Design Thinking sessions"""
    
    def __init__(self):
        self.activity_cache_timeout = 600  # 10 minutes
    
    def track_session_activity(self, session_code: str, activity_type: str, details: Dict[str, Any] = None):
        """Track session activity for monitoring dashboard"""
        try:
            activity_data = {
                'timestamp': timezone.now().isoformat(),
                'activity_type': activity_type,
                'details': details or {},
                'session_code': session_code
            }
            
            # Log activity
            logger.info(f"📊 Session Activity - {session_code}: {activity_type}", extra={
                'session_code': session_code,
                'activity_type': activity_type,
                'details': details
            })
            
            # Cache recent activity for quick access
            cache_key = f"session_activity_{session_code}"
            recent_activities = cache.get(cache_key, [])
            
            # Add new activity and keep only last 50
            recent_activities.append(activity_data)
            recent_activities = recent_activities[-50:]
            
            cache.set(cache_key, recent_activities, self.activity_cache_timeout)
            
        except Exception as e:
            logger.error(f"Error tracking session activity: {str(e)}")
    
    def get_session_activity(self, session_code: str, limit: int = 20) -> list:
        """Get recent activity for a session"""
        try:
            cache_key = f"session_activity_{session_code}"
            activities = cache.get(cache_key, [])
            return activities[-limit:] if activities else []
        except Exception as e:
            logger.error(f"Error getting session activity: {str(e)}")
            return []
    
    def track_error_occurrence(self, error_type: str, session_code: str = None, details: Dict[str, Any] = None):
        """Track error occurrences for monitoring"""
        try:
            error_data = {
                'timestamp': timezone.now().isoformat(),
                'error_type': error_type,
                'session_code': session_code,
                'details': details or {}
            }
            
            # Log error with structured data
            logger.error(f"🚨 Error Occurrence - {error_type}", extra=error_data)
            
            # Cache for error dashboard
            cache_key = "recent_errors"
            recent_errors = cache.get(cache_key, [])
            recent_errors.append(error_data)
            recent_errors = recent_errors[-100:]  # Keep last 100 errors
            
            cache.set(cache_key, recent_errors, 3600)  # 1 hour
            
        except Exception as e:
            logger.error(f"Error tracking error occurrence: {str(e)}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        try:
            # Get error rate from last hour
            recent_errors = cache.get("recent_errors", [])
            cutoff_time = timezone.now() - timedelta(hours=1)
            
            recent_error_count = sum(
                1 for error in recent_errors 
                if datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00')) > cutoff_time
            )
            
            # Get active sessions count (would need to query database)
            from .models import DesignThinkingSession
            active_sessions = DesignThinkingSession.objects.filter(
                is_active=True,
                created_at__gte=timezone.now() - timedelta(days=1)
            ).count()
            
            # Cache hit rate
            cache_stats = self._get_cache_stats()
            
            return {
                'timestamp': timezone.now().isoformat(),
                'error_rate_1h': recent_error_count,
                'active_sessions_24h': active_sessions,
                'cache_stats': cache_stats,
                'status': 'healthy' if recent_error_count < 10 else 'degraded'
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {
                'timestamp': timezone.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            # Basic cache test
            test_key = f"cache_test_{int(time.time())}"
            cache.set(test_key, "test", 60)
            cache_working = cache.get(test_key) == "test"
            cache.delete(test_key)
            
            return {
                'cache_working': cache_working,
                'backend': cache.__class__.__name__
            }
        except Exception as e:
            return {
                'cache_working': False,
                'error': str(e)
            }


class WebSocketConnectionMonitor:
    """Monitor WebSocket connection health and performance"""
    
    def __init__(self):
        self.connection_cache_timeout = 300  # 5 minutes
    
    def track_connection_event(self, session_code: str, event_type: str, connection_id: str = None, details: Dict[str, Any] = None):
        """Track WebSocket connection events"""
        try:
            event_data = {
                'timestamp': timezone.now().isoformat(),
                'event_type': event_type,
                'connection_id': connection_id,
                'details': details or {}
            }
            
            logger.info(f"🔌 WebSocket Event - {session_code}: {event_type}", extra={
                'session_code': session_code,
                'event_type': event_type,
                'connection_id': connection_id
            })
            
            # Track connection stats
            cache_key = f"ws_stats_{session_code}"
            stats = cache.get(cache_key, {
                'total_connections': 0,
                'current_connections': 0,
                'total_disconnections': 0,
                'error_count': 0,
                'last_activity': None
            })
            
            if event_type == 'connect':
                stats['total_connections'] += 1
                stats['current_connections'] += 1
            elif event_type == 'disconnect':
                stats['total_disconnections'] += 1
                stats['current_connections'] = max(0, stats['current_connections'] - 1)
            elif event_type == 'error':
                stats['error_count'] += 1
            
            stats['last_activity'] = timezone.now().isoformat()
            
            cache.set(cache_key, stats, self.connection_cache_timeout)
            
        except Exception as e:
            logger.error(f"Error tracking WebSocket event: {str(e)}")
    
    def get_connection_stats(self, session_code: str) -> Dict[str, Any]:
        """Get WebSocket connection statistics for session"""
        cache_key = f"ws_stats_{session_code}"
        return cache.get(cache_key, {})


# Global monitor instances
performance_monitor = PerformanceMonitor()
activity_monitor = SessionActivityMonitor()
connection_monitor = WebSocketConnectionMonitor()


def log_operation(operation_name: str):
    """Decorator for tracking operations with performance monitoring"""
    return performance_monitor.track_operation(operation_name)


def log_session_activity(session_code: str, activity_type: str, details: Dict[str, Any] = None):
    """Helper function to log session activity"""
    activity_monitor.track_session_activity(session_code, activity_type, details)


def log_error(error_type: str, session_code: str = None, details: Dict[str, Any] = None):
    """Helper function to log errors"""
    activity_monitor.track_error_occurrence(error_type, session_code, details)


def log_websocket_event(session_code: str, event_type: str, connection_id: str = None, details: Dict[str, Any] = None):
    """Helper function to log WebSocket events"""
    connection_monitor.track_connection_event(session_code, event_type, connection_id, details)