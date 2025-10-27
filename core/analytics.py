"""
DecipherWorld Analytics - DISABLED
All analytics functionality has been removed for performance optimization.
"""

import logging
from typing import Dict, Any, Optional
from django.http import HttpRequest

logger = logging.getLogger(__name__)

class DecipherWorldAnalytics:
    """
    Disabled analytics manager - all methods return True but do nothing
    """
    
    def __init__(self):
        """Initialize disabled analytics"""
        logger.info("Analytics disabled for performance optimization")
    
    def track_event(self, event_name: str, properties: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """Disabled - returns True"""
        return True
    
    def track_page_view(self, request: HttpRequest, page_name: str, additional_props: Optional[Dict[str, Any]] = None) -> bool:
        """Disabled - returns True"""
        return True
    
    def track_form_submission(self, request: HttpRequest, form_name: str, form_data: Optional[Dict[str, Any]] = None, success: bool = True) -> bool:
        """Disabled - returns True"""
        return True
    
    def track_game_session(self, request: HttpRequest, action: str, game_type: str, session_data: Optional[Dict[str, Any]] = None) -> bool:
        """Disabled - returns True"""
        return True
    
    def track_user_content_creation(self, request: HttpRequest, content_type: str, content_data: Optional[Dict[str, Any]] = None) -> bool:
        """Disabled - returns True"""
        return True
    
    def track_error(self, request: HttpRequest, error_type: str, error_message: str, additional_context: Optional[Dict[str, Any]] = None) -> bool:
        """Disabled - returns True"""
        return True
    
    def track_api_call(self, request: HttpRequest, endpoint: str, success: bool = True, response_time: Optional[float] = None) -> bool:
        """Disabled - returns True"""
        return True
    
    def track_achievement(self, request: HttpRequest, achievement_name: str, game_type: str, achievement_data: Optional[Dict[str, Any]] = None) -> bool:
        """Disabled - returns True"""
        return True

# Global analytics instance
analytics = DecipherWorldAnalytics()

# Convenience functions for easy importing - all disabled
def track_event(event_name: str, properties: Dict[str, Any], user_id: Optional[str] = None) -> bool:
    """Disabled - returns True"""
    return True

def track_page_view(request: HttpRequest, page_name: str, additional_props: Optional[Dict[str, Any]] = None) -> bool:
    """Disabled - returns True"""
    return True

def track_form_submission(request: HttpRequest, form_name: str, form_data: Optional[Dict[str, Any]] = None, success: bool = True) -> bool:
    """Disabled - returns True"""
    return True

def track_game_session(request: HttpRequest, action: str, game_type: str, session_data: Optional[Dict[str, Any]] = None) -> bool:
    """Disabled - returns True"""
    return True

def track_error(request: HttpRequest, error_type: str, error_message: str, additional_context: Optional[Dict[str, Any]] = None) -> bool:
    """Disabled - returns True"""
    return True

def track_user_content_creation(request: HttpRequest, content_type: str, content_data: Optional[Dict[str, Any]] = None) -> bool:
    """Disabled - returns True"""
    return True

def track_custom_event(request: HttpRequest, event_name: str, properties: Optional[Dict[str, Any]] = None) -> bool:
    """Disabled - returns True"""
    return True