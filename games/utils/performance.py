"""
DecipherWorld Performance Optimization Utilities
Database optimization, caching, and query performance tools
"""

from django.db import models, connection
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from typing import Dict, List, Any, Optional, Callable
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class GameCacheManager:
    """
    Intelligent caching system for game data
    Provides efficient caching with automatic invalidation
    """
    
    # Cache timeouts (in seconds)
    TIMEOUT_SHORT = 60       # 1 minute - frequently changing data
    TIMEOUT_MEDIUM = 300     # 5 minutes - session data
    TIMEOUT_LONG = 1800      # 30 minutes - game configurations
    TIMEOUT_EXTENDED = 3600  # 1 hour - static game data
    
    @classmethod
    def cache_session_data(cls, session_id: int, data: dict, timeout: int = None) -> bool:
        """Cache session data with automatic invalidation"""
        cache_key = f"game_session_{session_id}"
        timeout = timeout or cls.TIMEOUT_MEDIUM
        
        try:
            return cache.set(cache_key, data, timeout)
        except Exception as e:
            logger.warning(f"Failed to cache session data: {e}")
            return False
    
    @classmethod
    def get_session_data(cls, session_id: int) -> Optional[dict]:
        """Retrieve cached session data"""
        cache_key = f"game_session_{session_id}"
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Failed to retrieve session data from cache: {e}")
            return None
    
    @classmethod
    def cache_leaderboard(cls, game_type: str, session_id: int, data: list, timeout: int = None) -> bool:
        """Cache leaderboard data"""
        cache_key = f"leaderboard_{game_type}_{session_id}"
        timeout = timeout or cls.TIMEOUT_SHORT
        
        try:
            return cache.set(cache_key, data, timeout)
        except Exception as e:
            logger.warning(f"Failed to cache leaderboard: {e}")
            return False
    
    @classmethod
    def get_leaderboard(cls, game_type: str, session_id: int) -> Optional[list]:
        """Retrieve cached leaderboard"""
        cache_key = f"leaderboard_{game_type}_{session_id}"
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Failed to retrieve leaderboard from cache: {e}")
            return None
    
    @classmethod
    def invalidate_session_cache(cls, session_id: int):
        """Invalidate all cache entries for a session"""
        keys_to_delete = [
            f"game_session_{session_id}",
            f"leaderboard_*_{session_id}",
            f"player_data_{session_id}_*",
        ]
        
        try:
            # For pattern-based deletion, we need to get all keys first
            # This is a simplified approach - in production, use Redis SCAN
            cache.delete_many([f"game_session_{session_id}"])
            logger.info(f"Invalidated cache for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate session cache: {e}")
    
    @classmethod
    def cache_player_data(cls, session_id: int, player_id: int, data: dict, timeout: int = None) -> bool:
        """Cache player-specific data"""
        cache_key = f"player_data_{session_id}_{player_id}"
        timeout = timeout or cls.TIMEOUT_MEDIUM
        
        try:
            return cache.set(cache_key, data, timeout)
        except Exception as e:
            logger.warning(f"Failed to cache player data: {e}")
            return False
    
    @classmethod
    def get_player_data(cls, session_id: int, player_id: int) -> Optional[dict]:
        """Retrieve cached player data"""
        cache_key = f"player_data_{session_id}_{player_id}"
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Failed to retrieve player data from cache: {e}")
            return None


class QueryOptimizer:
    """
    Database query optimization utilities
    Provides tools for efficient querying and performance monitoring
    """
    
    @staticmethod
    def optimize_session_queries(session_model):
        """Add optimizations for session queries"""
        return session_model.objects.select_related().prefetch_related('players')
    
    @staticmethod
    def optimize_player_queries(player_model):
        """Add optimizations for player queries"""
        return player_model.objects.select_related('session').prefetch_related('actions')
    
    @staticmethod
    def get_active_sessions_optimized(session_model):
        """Get active sessions with optimized queries"""
        return session_model.objects.filter(
            status__in=['waiting', 'in_progress']
        ).select_related().prefetch_related(
            'players'
        ).annotate(
            active_player_count=models.Count('players', filter=models.Q(players__is_active=True))
        )
    
    @staticmethod
    def get_session_leaderboard_optimized(session, player_model):
        """Get session leaderboard with optimized query"""
        return player_model.objects.filter(
            session=session,
            is_active=True
        ).select_related('session').order_by('-total_score', 'joined_at')[:10]
    
    @staticmethod
    def get_player_statistics_optimized(player_model, session_id: int):
        """Get player statistics with single query"""
        return player_model.objects.filter(
            session_id=session_id,
            is_active=True
        ).aggregate(
            total_players=models.Count('id'),
            average_score=models.Avg('total_score'),
            highest_score=models.Max('total_score'),
            total_actions=models.Sum('actions_completed')
        )


class PerformanceMonitor:
    """
    Performance monitoring and logging
    Tracks query performance, response times, and system metrics
    """
    
    def __init__(self):
        self.query_times = []
        self.start_time = None
    
    def start_monitoring(self):
        """Start monitoring performance"""
        self.start_time = time.time()
        self.query_times = []
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return metrics"""
        if not self.start_time:
            return {}
        
        end_time = time.time()
        total_time = end_time - self.start_time
        
        metrics = {
            'total_time': total_time,
            'query_count': len(connection.queries) if hasattr(connection, 'queries') else 0,
            'timestamp': timezone.now().isoformat(),
        }
        
        # Add query analysis if DEBUG is True
        if settings.DEBUG and hasattr(connection, 'queries'):
            query_times = [float(q['time']) for q in connection.queries]
            metrics.update({
                'total_query_time': sum(query_times),
                'average_query_time': sum(query_times) / len(query_times) if query_times else 0,
                'slowest_query': max(query_times) if query_times else 0,
            })
        
        return metrics
    
    def log_performance(self, operation_name: str, metrics: Dict[str, Any]):
        """Log performance metrics"""
        logger.info(f"Performance - {operation_name}: {metrics}")


def cache_game_data(timeout: int = GameCacheManager.TIMEOUT_MEDIUM, 
                   key_prefix: str = "game_data"):
    """
    Decorator for caching game data
    Automatically caches function results with intelligent key generation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}_{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cached result for {cache_key}")
            
            return result
        return wrapper
    return decorator


def monitor_performance(operation_name: str = None):
    """
    Decorator for monitoring function performance
    Logs execution time and query counts
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = PerformanceMonitor()
            monitor.start_monitoring()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                metrics = monitor.stop_monitoring()
                name = operation_name or f"{func.__module__}.{func.__name__}"
                monitor.log_performance(name, metrics)
        
        return wrapper
    return decorator


class DatabaseIndexOptimizer:
    """
    Database index optimization utilities
    Analyzes queries and suggests optimal indexes
    """
    
    @staticmethod
    def get_recommended_indexes() -> List[Dict[str, Any]]:
        """Get recommended indexes for game models"""
        recommendations = [
            {
                'model': 'GameSession',
                'fields': ['session_code', 'status'],
                'type': 'composite',
                'reason': 'Frequent lookups by session code and status filtering'
            },
            {
                'model': 'GamePlayer',
                'fields': ['session', 'is_active'],
                'type': 'composite',
                'reason': 'Player counting and active player filtering'
            },
            {
                'model': 'GamePlayer',
                'fields': ['last_activity'],
                'type': 'simple',
                'reason': 'Online status checking and cleanup'
            },
            {
                'model': 'GameAction',
                'fields': ['player', 'created_at'],
                'type': 'composite',
                'reason': 'Player action history and timeline queries'
            },
            {
                'model': 'GameAction',
                'fields': ['action_type'],
                'type': 'simple',
                'reason': 'Action type filtering and analytics'
            },
        ]
        
        return recommendations
    
    @staticmethod
    def generate_index_migration(model_name: str, indexes: List[Dict]) -> str:
        """Generate Django migration code for indexes"""
        migration_code = f"""
# Generated index migration for {model_name}
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        # Add your dependencies here
    ]
    
    operations = [
"""
        
        for index in indexes:
            if index['type'] == 'composite':
                migration_code += f"""
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_{model_name.lower()}_{('_'.join(index['fields']))} ON {model_name.lower()} ({', '.join(index['fields'])});",
            reverse_sql="DROP INDEX IF EXISTS idx_{model_name.lower()}_{('_'.join(index['fields']))};",
        ),
"""
            else:
                field = index['fields'][0]
                migration_code += f"""
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_{model_name.lower()}_{field} ON {model_name.lower()} ({field});",
            reverse_sql="DROP INDEX IF EXISTS idx_{model_name.lower()}_{field};",
        ),
"""
        
        migration_code += """
    ]
"""
        return migration_code


class GameMetricsCollector:
    """
    Collect and analyze game performance metrics
    Provides insights for optimization
    """
    
    @staticmethod
    def collect_session_metrics(session) -> Dict[str, Any]:
        """Collect comprehensive session metrics"""
        metrics = {
            'session_id': session.id,
            'session_code': session.session_code,
            'status': session.status,
            'created_at': session.created_at.isoformat(),
            'player_count': session.player_count,
        }
        
        # Add performance metrics if available
        if hasattr(session, 'players'):
            players = session.players.filter(is_active=True)
            if players.exists():
                metrics.update({
                    'average_score': players.aggregate(avg=models.Avg('total_score'))['avg'],
                    'highest_score': players.aggregate(max=models.Max('total_score'))['max'],
                    'total_actions': players.aggregate(sum=models.Sum('actions_completed'))['sum'],
                })
        
        return metrics
    
    @staticmethod
    def analyze_query_performance() -> Dict[str, Any]:
        """Analyze database query performance"""
        if not settings.DEBUG:
            return {'message': 'Query analysis only available in DEBUG mode'}
        
        if not hasattr(connection, 'queries'):
            return {'message': 'No query data available'}
        
        queries = connection.queries
        if not queries:
            return {'message': 'No queries recorded'}
        
        query_times = [float(q['time']) for q in queries]
        
        analysis = {
            'total_queries': len(queries),
            'total_time': sum(query_times),
            'average_time': sum(query_times) / len(query_times),
            'slowest_query': max(query_times),
            'fastest_query': min(query_times),
            'slow_queries': len([t for t in query_times if t > 0.1]),  # > 100ms
        }
        
        return analysis


# Enhanced caching decorators for specific game operations

@cache_game_data(timeout=GameCacheManager.TIMEOUT_SHORT, key_prefix="leaderboard")
def get_cached_leaderboard(session_id: int, game_type: str):
    """Cached leaderboard retrieval"""
    # This function would be implemented by specific games
    pass


@cache_game_data(timeout=GameCacheManager.TIMEOUT_MEDIUM, key_prefix="session_state")
def get_cached_session_state(session_id: int):
    """Cached session state retrieval"""
    # This function would be implemented by specific games
    pass


@monitor_performance("game_action_processing")
def process_game_action_with_monitoring(session, player, action_data):
    """Process game action with automatic performance monitoring"""
    # This function would be implemented by specific games
    pass