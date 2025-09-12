"""
Caching utilities for Constitution Challenge optimization
"""

import json
import hashlib
from django.core.cache import cache
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from typing import Optional, Dict, Any, List

from .models import ConstitutionTeam, CountryState, ConstitutionAnswer, GameSession


class CacheKeys:
    """Centralized cache key management"""
    
    TEAM_STATE = "team_state:{team_id}"
    TEAM_LEADERBOARD = "leaderboard:{session_id}"
    TEAM_ANSWERS = "team_answers:{team_id}"
    SESSION_STATE = "session_state:{session_code}"
    QUESTION_DATA = "question_data:{question_id}"
    TEAM_PROGRESS = "team_progress:{team_id}"
    VISUAL_STATE = "visual_state:{team_id}"
    
    @classmethod
    def get_key(cls, template: str, **kwargs) -> str:
        """Generate cache key with parameters"""
        return template.format(**kwargs)


class ConstitutionCache:
    """High-performance caching for Constitution Challenge"""
    
    # Cache timeouts (in seconds)
    TIMEOUT_SHORT = 300      # 5 minutes - frequently changing data
    TIMEOUT_MEDIUM = 900     # 15 minutes - session data
    TIMEOUT_LONG = 3600      # 1 hour - static data
    TIMEOUT_VERY_LONG = 86400  # 24 hours - rarely changing data
    
    @staticmethod
    def get_team_state(team_id: int, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get comprehensive team state with caching"""
        cache_key = CacheKeys.get_key(CacheKeys.TEAM_STATE, team_id=team_id)
        
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
        
        try:
            from .models import ConstitutionTeam
            team = ConstitutionTeam.objects.select_related(
                'session__game',
                'country_state'
            ).prefetch_related(
                'answers__question',
                'answers__chosen_option'
            ).get(id=team_id)
            
            team_data = {
                'id': team.id,
                'team_name': team.team_name,
                'country_name': team.country_name,
                'total_score': team.total_score,
                'questions_completed': team.questions_completed,
                'is_completed': team.is_completed,
                'completion_time': team.completion_time.isoformat() if team.completion_time else None,
                'team_avatar': team.team_avatar,
                'flag_emoji': team.flag_emoji,
                'country_color': team.country_color,
                'session_id': team.session.id,
                'session_code': team.session.session_code,
            }
            
            # Add country state if available
            if hasattr(team, 'country_state') and team.country_state:
                team_data['country_state'] = {
                    'current_city_level': team.country_state.current_city_level,
                    'democracy_score': team.country_state.democracy_score,
                    'fairness_score': team.country_state.fairness_score,
                    'freedom_score': team.country_state.freedom_score,
                    'stability_score': team.country_state.stability_score,
                    'visual_elements': team.country_state.visual_elements,
                }
            
            # Cache the data
            cache.set(cache_key, team_data, ConstitutionCache.TIMEOUT_SHORT)
            return team_data
            
        except Exception as e:
            print(f"Cache error getting team state: {e}")
            return None
    
    @staticmethod
    def get_session_leaderboard(session_id: int, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get session leaderboard with caching"""
        cache_key = CacheKeys.get_key(CacheKeys.TEAM_LEADERBOARD, session_id=session_id)
        
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
        
        try:
            from .models import ConstitutionTeam
            teams = ConstitutionTeam.objects.filter(
                session_id=session_id
            ).select_related('country_state').order_by(
                '-total_score', 'completion_time'
            )[:10]  # Top 10 teams
            
            leaderboard_data = []
            for rank, team in enumerate(teams, 1):
                leaderboard_data.append({
                    'rank': rank,
                    'id': team.id,
                    'team_name': team.team_name,
                    'country_name': team.country_name,
                    'total_score': team.total_score,
                    'team_avatar': team.team_avatar,
                    'flag_emoji': team.flag_emoji,
                    'country_color': team.country_color,
                    'questions_completed': team.questions_completed,
                    'is_completed': team.is_completed,
                    'governance_level': team.get_governance_level()['description'] if hasattr(team, 'get_governance_level') else 'Unknown'
                })
            
            # Cache for a shorter time since leaderboard changes frequently
            cache.set(cache_key, leaderboard_data, ConstitutionCache.TIMEOUT_SHORT)
            return leaderboard_data
            
        except Exception as e:
            print(f"Cache error getting leaderboard: {e}")
            return []
    
    @staticmethod
    def get_team_visual_state(team_id: int, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get team visual state for city rendering"""
        cache_key = CacheKeys.get_key(CacheKeys.VISUAL_STATE, team_id=team_id)
        
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
        
        try:
            from .models import CountryState
            country_state = CountryState.objects.select_related('team').get(team_id=team_id)
            
            visual_data = {
                'current_city_level': country_state.current_city_level,
                'democracy_score': country_state.democracy_score,
                'fairness_score': country_state.fairness_score,
                'freedom_score': country_state.freedom_score,
                'stability_score': country_state.stability_score,
                'visual_elements': country_state.visual_elements,
                'visual_features_unlocked': country_state.visual_features_unlocked,
            }
            
            # Cache visual state for medium duration
            cache.set(cache_key, visual_data, ConstitutionCache.TIMEOUT_MEDIUM)
            return visual_data
            
        except Exception as e:
            print(f"Cache error getting visual state: {e}")
            return None
    
    @staticmethod
    def invalidate_team_cache(team_id: int):
        """Invalidate all cache entries for a specific team"""
        cache_keys = [
            CacheKeys.get_key(CacheKeys.TEAM_STATE, team_id=team_id),
            CacheKeys.get_key(CacheKeys.TEAM_ANSWERS, team_id=team_id),
            CacheKeys.get_key(CacheKeys.TEAM_PROGRESS, team_id=team_id),
            CacheKeys.get_key(CacheKeys.VISUAL_STATE, team_id=team_id),
        ]
        
        cache.delete_many(cache_keys)
        print(f"Invalidated cache for team {team_id}")
    
    @staticmethod
    def invalidate_session_cache(session_id: int):
        """Invalidate cache entries for a session"""
        cache_keys = [
            CacheKeys.get_key(CacheKeys.TEAM_LEADERBOARD, session_id=session_id),
        ]
        
        cache.delete_many(cache_keys)
        print(f"Invalidated session cache for session {session_id}")
    
    @staticmethod
    def warm_cache_for_session(session_id: int):
        """Pre-warm cache for an active session"""
        try:
            # Pre-load leaderboard
            ConstitutionCache.get_session_leaderboard(session_id, use_cache=False)
            
            # Pre-load team states for active teams
            from .models import ConstitutionTeam
            active_teams = ConstitutionTeam.objects.filter(
                session_id=session_id,
                is_completed=False
            ).values_list('id', flat=True)[:20]  # Limit to prevent overload
            
            for team_id in active_teams:
                ConstitutionCache.get_team_state(team_id, use_cache=False)
                ConstitutionCache.get_team_visual_state(team_id, use_cache=False)
                
            print(f"Cache warmed for session {session_id}")
            
        except Exception as e:
            print(f"Error warming cache: {e}")


# Signal handlers for automatic cache invalidation
@receiver(post_save, sender=ConstitutionTeam)
def invalidate_team_cache_on_update(sender, instance, **kwargs):
    """Invalidate cache when team is updated"""
    ConstitutionCache.invalidate_team_cache(instance.id)
    ConstitutionCache.invalidate_session_cache(instance.session.id)


@receiver(post_save, sender=CountryState)
def invalidate_visual_cache_on_update(sender, instance, **kwargs):
    """Invalidate visual cache when country state is updated"""
    ConstitutionCache.invalidate_team_cache(instance.team.id)


@receiver(post_save, sender=ConstitutionAnswer)
def invalidate_cache_on_answer(sender, instance, **kwargs):
    """Invalidate cache when new answer is submitted"""
    ConstitutionCache.invalidate_team_cache(instance.team.id)
    ConstitutionCache.invalidate_session_cache(instance.team.session.id)


# Utility decorator for caching view responses
def cache_view_response(timeout=300, key_prefix='view'):
    """Decorator to cache view responses"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Create cache key based on view name and parameters
            cache_key_parts = [key_prefix, view_func.__name__] + [str(arg) for arg in args]
            if hasattr(request, 'user') and request.user.is_authenticated:
                cache_key_parts.append(f"user_{request.user.id}")
            
            cache_key = hashlib.md5(":".join(cache_key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
            
            # Execute view and cache result
            response = view_func(request, *args, **kwargs)
            cache.set(cache_key, response, timeout)
            
            return response
        return wrapper
    return decorator