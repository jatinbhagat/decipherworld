"""
Administrative views for monitoring and managing simplified Design Thinking sessions
Provides real-time monitoring, performance metrics, and system health dashboards
"""

import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views import View
from django.utils import timezone
from datetime import timedelta

from .monitoring import (
    performance_monitor, activity_monitor, connection_monitor
)
from .models import (
    DesignThinkingSession, SimplifiedPhaseInput, 
    PhaseCompletionTracker, DesignTeam
)


@method_decorator(staff_member_required, name='dispatch')
class SystemMonitoringDashboard(TemplateView):
    """
    Comprehensive system monitoring dashboard for administrators
    Shows performance metrics, error rates, and system health
    """
    template_name = 'group_learning/admin/monitoring_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Get system health overview
            system_health = activity_monitor.get_system_health()
            
            # Get performance metrics
            performance_metrics = performance_monitor.get_all_metrics()
            
            # Get recent errors
            recent_errors = self._get_recent_errors()
            
            # Get active sessions summary
            active_sessions = self._get_active_sessions_summary()
            
            context.update({
                'system_health': system_health,
                'performance_metrics': performance_metrics,
                'recent_errors': recent_errors,
                'active_sessions': active_sessions,
                'refresh_interval': 30,  # seconds
                'last_updated': timezone.now().isoformat()
            })
            
        except Exception as e:
            context['error'] = f'Error loading monitoring data: {str(e)}'
        
        return context
    
    def _get_recent_errors(self, hours=1):
        """Get recent errors for dashboard"""
        try:
            from django.core.cache import cache
            recent_errors = cache.get("recent_errors", [])
            
            # Filter to last N hours
            cutoff_time = timezone.now() - timedelta(hours=hours)
            filtered_errors = [
                error for error in recent_errors
                if timezone.datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00')) > cutoff_time
            ]
            
            # Group by error type
            error_summary = {}
            for error in filtered_errors:
                error_type = error.get('error_type', 'unknown')
                if error_type not in error_summary:
                    error_summary[error_type] = {
                        'count': 0,
                        'sessions_affected': set(),
                        'last_occurrence': None
                    }
                
                error_summary[error_type]['count'] += 1
                if error.get('session_code'):
                    error_summary[error_type]['sessions_affected'].add(error['session_code'])
                error_summary[error_type]['last_occurrence'] = error['timestamp']
            
            # Convert sets to counts for JSON serialization
            for error_type in error_summary:
                error_summary[error_type]['sessions_affected'] = len(error_summary[error_type]['sessions_affected'])
            
            return {
                'total_errors': len(filtered_errors),
                'error_types': error_summary,
                'recent_errors': filtered_errors[-10:]  # Last 10 errors for detail view
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_active_sessions_summary(self):
        """Get summary of active sessions"""
        try:
            # Sessions active in last 24 hours
            cutoff_time = timezone.now() - timedelta(hours=24)
            
            active_sessions = DesignThinkingSession.objects.filter(
                is_active=True,
                created_at__gte=cutoff_time
            ).select_related('design_game').prefetch_related('design_teams')
            
            summary = {
                'total_active': active_sessions.count(),
                'simplified_sessions': 0,
                'total_teams': 0,
                'total_inputs_24h': 0,
                'sessions_with_activity': 0
            }
            
            for session in active_sessions:
                # Count simplified sessions (auto-advance enabled)
                if hasattr(session.design_game, 'auto_advance_enabled') and session.design_game.auto_advance_enabled:
                    summary['simplified_sessions'] += 1
                
                # Count teams
                summary['total_teams'] += session.design_teams.count()
                
                # Check for recent activity
                recent_inputs = SimplifiedPhaseInput.objects.filter(
                    session=session,
                    submitted_at__gte=cutoff_time
                ).count()
                
                summary['total_inputs_24h'] += recent_inputs
                if recent_inputs > 0:
                    summary['sessions_with_activity'] += 1
            
            return summary
            
        except Exception as e:
            return {'error': str(e)}


@method_decorator(staff_member_required, name='dispatch')
class SessionDetailMonitoringView(TemplateView):
    """
    Detailed monitoring view for a specific session
    Shows real-time activity, team progress, and performance metrics
    """
    template_name = 'group_learning/admin/session_monitoring.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs.get('session_code')
        
        try:
            session = DesignThinkingSession.objects.select_related(
                'design_game', 'current_mission'
            ).prefetch_related('design_teams').get(session_code=session_code)
            
            # Get session activity
            recent_activity = activity_monitor.get_session_activity(session_code, limit=50)
            
            # Get WebSocket connection stats
            connection_stats = connection_monitor.get_connection_stats(session_code)
            
            # Get team progress details
            team_progress = self._get_team_progress_details(session)
            
            # Get performance metrics for this session
            session_metrics = self._get_session_performance_metrics(session)
            
            context.update({
                'session': session,
                'recent_activity': recent_activity,
                'connection_stats': connection_stats,
                'team_progress': team_progress,
                'session_metrics': session_metrics,
                'refresh_interval': 5,  # seconds for session-specific monitoring
                'last_updated': timezone.now().isoformat()
            })
            
        except DesignThinkingSession.DoesNotExist:
            context['error'] = f'Session {session_code} not found'
        except Exception as e:
            context['error'] = f'Error loading session monitoring data: {str(e)}'
        
        return context
    
    def _get_team_progress_details(self, session):
        """Get detailed progress information for all teams"""
        try:
            teams_progress = []
            
            for team in session.design_teams.all():
                # Get completion tracking
                completion_data = PhaseCompletionTracker.objects.filter(
                    session=session,
                    team=team
                ).order_by('-updated_at').first()
                
                # Get recent inputs
                recent_inputs = SimplifiedPhaseInput.objects.filter(
                    team=team,
                    session=session,
                    submitted_at__gte=timezone.now() - timedelta(hours=1)
                ).count()
                
                # Get scoring status
                unscored_inputs = SimplifiedPhaseInput.objects.filter(
                    team=team,
                    session=session,
                    teacher_score__isnull=True
                ).count()
                
                teams_progress.append({
                    'team': {
                        'id': team.id,
                        'name': team.team_name,
                        'emoji': team.team_emoji,
                        'member_count': len(team.team_members or [])
                    },
                    'completion': {
                        'percentage': completion_data.completion_percentage if completion_data else 0,
                        'completed_inputs': completion_data.completed_inputs if completion_data else 0,
                        'total_required': completion_data.total_required_inputs if completion_data else 0,
                        'is_ready_to_advance': completion_data.is_ready_to_advance if completion_data else False
                    },
                    'activity': {
                        'recent_inputs_1h': recent_inputs,
                        'unscored_inputs': unscored_inputs
                    }
                })
            
            return teams_progress
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_session_performance_metrics(self, session):
        """Get performance metrics specific to this session"""
        try:
            # Calculate session-specific metrics
            total_inputs = SimplifiedPhaseInput.objects.filter(session=session).count()
            
            # Average completion time
            from django.db import models
            avg_completion_time = SimplifiedPhaseInput.objects.filter(
                session=session,
                time_to_complete_seconds__gt=0
            ).aggregate(
                avg_time=models.Avg('time_to_complete_seconds')
            )['avg_time'] or 0
            
            # Scoring statistics
            scoring_stats = SimplifiedPhaseInput.objects.filter(
                session=session
            ).aggregate(
                total_inputs=models.Count('id'),
                scored_inputs=models.Count('teacher_score'),
                avg_score=models.Avg('teacher_score')
            )
            
            return {
                'total_inputs': total_inputs,
                'avg_completion_time_seconds': round(avg_completion_time, 2),
                'scoring_rate': round(
                    (scoring_stats['scored_inputs'] / max(scoring_stats['total_inputs'], 1)) * 100, 1
                ) if scoring_stats['total_inputs'] else 0,
                'session_duration_minutes': round(
                    (timezone.now() - session.created_at).total_seconds() / 60, 1
                )
            }
            
        except Exception as e:
            return {'error': str(e)}


@method_decorator(staff_member_required, name='dispatch')
class MonitoringAPIView(View):
    """
    API endpoint for real-time monitoring data
    Returns JSON data for AJAX updates
    """
    
    def get(self, request, *args, **kwargs):
        data_type = request.GET.get('type', 'system_health')
        session_code = request.GET.get('session_code')
        
        try:
            if data_type == 'system_health':
                data = activity_monitor.get_system_health()
            elif data_type == 'performance_metrics':
                data = performance_monitor.get_all_metrics()
            elif data_type == 'session_activity' and session_code:
                limit = int(request.GET.get('limit', 20))
                data = activity_monitor.get_session_activity(session_code, limit)
            elif data_type == 'connection_stats' and session_code:
                data = connection_monitor.get_connection_stats(session_code)
            else:
                return JsonResponse({'error': 'Invalid data type or missing session_code'}, status=400)
            
            return JsonResponse({
                'success': True,
                'data': data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=500)


# Utility function for quick system status check
def get_system_status_summary():
    """Get a quick summary of system status for external monitoring"""
    try:
        health = activity_monitor.get_system_health()
        metrics = performance_monitor.get_all_metrics()
        
        return {
            'status': health.get('status', 'unknown'),
            'error_rate_1h': health.get('error_rate_1h', 0),
            'active_sessions': health.get('active_sessions_24h', 0),
            'cache_working': health.get('cache_stats', {}).get('cache_working', False),
            'timestamp': timezone.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }