"""
Design Thinking Game Caching Layer
Optimized caching for session progress, mission data, and team submissions
"""

from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Q
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class DesignThinkingCache:
    """
    Centralized caching for Design Thinking game operations
    Provides intelligent caching with automatic invalidation
    """
    
    # Cache key prefixes
    SESSION_PROGRESS_PREFIX = 'dt_session_progress'
    MISSION_DATA_PREFIX = 'dt_mission_data'
    TEAM_SUBMISSIONS_PREFIX = 'dt_team_submissions'
    FACILITATOR_DASHBOARD_PREFIX = 'dt_facilitator_dash'
    
    # Cache timeouts (in seconds)
    PROGRESS_TIMEOUT = 60  # 1 minute for progress data
    MISSION_TIMEOUT = 300  # 5 minutes for mission structure (rarely changes)
    SUBMISSION_TIMEOUT = 30  # 30 seconds for submission counts
    DASHBOARD_TIMEOUT = 45  # 45 seconds for facilitator dashboard data
    
    @classmethod
    def get_session_progress(cls, session_code):
        """
        Get cached session progress data
        
        Args:
            session_code (str): Session code
            
        Returns:
            dict or None: Cached progress data or None if not cached
        """
        cache_key = f"{cls.SESSION_PROGRESS_PREFIX}:{session_code}"
        data = cache.get(cache_key)
        
        if data:
            logger.debug(f"Cache HIT for session progress: {session_code}")
            return data
        
        logger.debug(f"Cache MISS for session progress: {session_code}")
        return None
    
    @classmethod
    def set_session_progress(cls, session_code, progress_data):
        """
        Cache session progress data
        
        Args:
            session_code (str): Session code
            progress_data (dict): Progress data to cache
        """
        cache_key = f"{cls.SESSION_PROGRESS_PREFIX}:{session_code}"
        
        # Add timestamp for debugging
        progress_data['cached_at'] = timezone.now().isoformat()
        
        cache.set(cache_key, progress_data, cls.PROGRESS_TIMEOUT)
        logger.debug(f"Cached session progress for {session_code} (expires in {cls.PROGRESS_TIMEOUT}s)")
    
    @classmethod
    def invalidate_session_progress(cls, session_code):
        """
        Invalidate cached session progress
        
        Args:
            session_code (str): Session code
        """
        cache_key = f"{cls.SESSION_PROGRESS_PREFIX}:{session_code}"
        cache.delete(cache_key)
        logger.info(f"Invalidated session progress cache for {session_code}")
    
    @classmethod
    def get_mission_data(cls, game_id):
        """
        Get cached mission structure data
        
        Args:
            game_id (int): Design thinking game ID
            
        Returns:
            list or None: Cached mission data or None if not cached
        """
        cache_key = f"{cls.MISSION_DATA_PREFIX}:{game_id}"
        data = cache.get(cache_key)
        
        if data:
            logger.debug(f"Cache HIT for mission data: game {game_id}")
            return data
        
        logger.debug(f"Cache MISS for mission data: game {game_id}")
        return None
    
    @classmethod
    def set_mission_data(cls, game_id, mission_data):
        """
        Cache mission structure data
        
        Args:
            game_id (int): Design thinking game ID
            mission_data (list): Mission data to cache
        """
        cache_key = f"{cls.MISSION_DATA_PREFIX}:{game_id}"
        cache.set(cache_key, mission_data, cls.MISSION_TIMEOUT)
        logger.debug(f"Cached mission data for game {game_id} (expires in {cls.MISSION_TIMEOUT}s)")
    
    @classmethod
    def get_team_submissions_count(cls, team_id, mission_id):
        """
        Get cached team submission count
        
        Args:
            team_id (int): Team ID
            mission_id (int): Mission ID
            
        Returns:
            int or None: Submission count or None if not cached
        """
        cache_key = f"{cls.TEAM_SUBMISSIONS_PREFIX}:{team_id}:{mission_id}"
        count = cache.get(cache_key)
        
        if count is not None:
            logger.debug(f"Cache HIT for submissions: team {team_id}, mission {mission_id}")
            return count
        
        logger.debug(f"Cache MISS for submissions: team {team_id}, mission {mission_id}")
        return None
    
    @classmethod
    def set_team_submissions_count(cls, team_id, mission_id, count):
        """
        Cache team submission count
        
        Args:
            team_id (int): Team ID
            mission_id (int): Mission ID
            count (int): Submission count
        """
        cache_key = f"{cls.TEAM_SUBMISSIONS_PREFIX}:{team_id}:{mission_id}"
        cache.set(cache_key, count, cls.SUBMISSION_TIMEOUT)
        logger.debug(f"Cached submission count for team {team_id}, mission {mission_id}: {count}")
    
    @classmethod
    def invalidate_team_submissions(cls, team_id, mission_id=None):
        """
        Invalidate cached submission count for a team
        
        Args:
            team_id (int): Team ID
            mission_id (int, optional): Specific mission ID or None to clear all missions
        """
        if mission_id:
            cache_key = f"{cls.TEAM_SUBMISSIONS_PREFIX}:{team_id}:{mission_id}"
            cache.delete(cache_key)
            logger.debug(f"Invalidated submission cache for team {team_id}, mission {mission_id}")
        else:
            # Invalidate all missions for this team (less efficient but more thorough)
            # In production, consider using cache versioning or tagging
            pattern = f"{cls.TEAM_SUBMISSIONS_PREFIX}:{team_id}:*"
            logger.debug(f"Would invalidate submission cache pattern: {pattern}")
    
    @classmethod
    def get_facilitator_dashboard_data(cls, session_code):
        """
        Get cached facilitator dashboard data
        
        Args:
            session_code (str): Session code
            
        Returns:
            dict or None: Dashboard data or None if not cached
        """
        cache_key = f"{cls.FACILITATOR_DASHBOARD_PREFIX}:{session_code}"
        data = cache.get(cache_key)
        
        if data:
            logger.debug(f"Cache HIT for facilitator dashboard: {session_code}")
            return data
        
        logger.debug(f"Cache MISS for facilitator dashboard: {session_code}")
        return None
    
    @classmethod
    def set_facilitator_dashboard_data(cls, session_code, dashboard_data):
        """
        Cache facilitator dashboard data
        
        Args:
            session_code (str): Session code
            dashboard_data (dict): Dashboard data to cache
        """
        cache_key = f"{cls.FACILITATOR_DASHBOARD_PREFIX}:{session_code}"
        
        # Add cache metadata
        dashboard_data['cache_metadata'] = {
            'cached_at': timezone.now().isoformat(),
            'expires_in': cls.DASHBOARD_TIMEOUT
        }
        
        cache.set(cache_key, dashboard_data, cls.DASHBOARD_TIMEOUT)
        logger.debug(f"Cached facilitator dashboard for {session_code}")
    
    @classmethod
    def invalidate_facilitator_dashboard(cls, session_code):
        """
        Invalidate cached facilitator dashboard data
        
        Args:
            session_code (str): Session code
        """
        cache_key = f"{cls.FACILITATOR_DASHBOARD_PREFIX}:{session_code}"
        cache.delete(cache_key)
        logger.info(f"Invalidated facilitator dashboard cache for {session_code}")
    
    @classmethod
    def invalidate_all_session_caches(cls, session_code):
        """
        Invalidate all caches related to a session
        
        Args:
            session_code (str): Session code
        """
        cls.invalidate_session_progress(session_code)
        cls.invalidate_facilitator_dashboard(session_code)
        logger.info(f"Invalidated all caches for session {session_code}")
    
    @classmethod
    def get_cache_stats(cls):
        """
        Get cache statistics for monitoring
        
        Returns:
            dict: Cache statistics
        """
        # Note: This is a simplified version. In production, consider using
        # Redis or Memcached with proper stats collection
        return {
            'cache_backend': cache.__class__.__name__,
            'prefixes': {
                'session_progress': cls.SESSION_PROGRESS_PREFIX,
                'mission_data': cls.MISSION_DATA_PREFIX,
                'team_submissions': cls.TEAM_SUBMISSIONS_PREFIX,
                'facilitator_dashboard': cls.FACILITATOR_DASHBOARD_PREFIX,
            },
            'timeouts': {
                'progress': cls.PROGRESS_TIMEOUT,
                'mission': cls.MISSION_TIMEOUT,
                'submission': cls.SUBMISSION_TIMEOUT,
                'dashboard': cls.DASHBOARD_TIMEOUT,
            }
        }


class CacheWarmer:
    """
    Utility for pre-warming caches with frequently accessed data
    """
    
    @staticmethod
    def warm_session_cache(session):
        """
        Pre-warm cache for a new session
        
        Args:
            session: DesignThinkingSession instance
        """
        from .services import DesignThinkingService
        
        try:
            service = DesignThinkingService(session)
            progress_data = service.get_session_progress()
            
            DesignThinkingCache.set_session_progress(
                session.session_code, 
                progress_data
            )
            
            logger.info(f"Pre-warmed cache for session {session.session_code}")
            
        except Exception as e:
            logger.error(f"Failed to warm cache for session {session.session_code}: {str(e)}")
    
    @staticmethod
    def warm_mission_cache(game):
        """
        Pre-warm mission data cache
        
        Args:
            game: DesignThinkingGame instance
        """
        try:
            missions = list(game.missions.filter(is_active=True).order_by('order').values(
                'id', 'title', 'order', 'description', 'mission_type'
            ))
            
            DesignThinkingCache.set_mission_data(game.id, missions)
            logger.info(f"Pre-warmed mission cache for game {game.id}")
            
        except Exception as e:
            logger.error(f"Failed to warm mission cache for game {game.id}: {str(e)}")