"""
DecipherWorld Backend Analytics
MixPanel integration for server-side event tracking
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from django.conf import settings
from django.http import HttpRequest
import mixpanel

logger = logging.getLogger(__name__)

class DecipherWorldAnalytics:
    """
    Backend analytics manager for tracking server-side events
    """
    
    def __init__(self):
        """Initialize MixPanel consumer with project credentials"""
        self.project_token = '100436c05647bbfab884ce5304fe0b65'
        self.api_secret = 'a82c3dec5943e408a721d1414280600c'
        
        # Initialize MixPanel consumer
        try:
            self.mp = mixpanel.Mixpanel(self.project_token)
            # Note: Consumer doesn't need api_secret, it's handled by the Mixpanel instance
            self.mp_consumer = mixpanel.Consumer()
            logger.info("MixPanel backend analytics initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MixPanel: {str(e)}")
            self.mp = None
            self.mp_consumer = None

    def get_user_id_from_request(self, request: HttpRequest) -> str:
        """
        Extract user ID from cookies or generate anonymous ID
        """
        user_id = request.COOKIES.get('dw_user_id')
        if not user_id:
            # Fallback to session-based ID if cookie not available
            if hasattr(request, 'session') and request.session.session_key:
                user_id = f"session_{request.session.session_key}"
            else:
                user_id = f"unknown_{datetime.now().timestamp()}"
        
        return user_id

    def get_base_properties(self, request: HttpRequest) -> Dict[str, Any]:
        """
        Get standard properties for all backend events
        """
        user_id = self.get_user_id_from_request(request)
        
        base_props = {
            'user_id': user_id,
            'login_status': 'Not Logged In',
            'timestamp': datetime.now().isoformat(),
            'source': 'backend',
            'current_page': request.path,
            'referrer': request.META.get('HTTP_REFERER', 'direct'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': self.get_client_ip(request),
            'method': request.method,
        }
        
        # Add session info if available
        if hasattr(request, 'session'):
            base_props['session_key'] = request.session.session_key or 'no-session'
        
        # Add game information if on a game page
        game_info = self.get_game_info_from_request(request)
        base_props.update(game_info)
        
        return base_props

    def get_game_info_from_request(self, request: HttpRequest) -> Dict[str, Any]:
        """
        Extract game information from request path
        """
        path = request.path
        game_info = {}

        # Design Thinking Game
        if '/learn/design-thinking/' in path or '/learn/session/' in path:
            game_info.update({
                'game_name': 'Design Thinking Challenge',
                'game_code': 'DTC001'
            })
            
            # Extract session ID if available
            import re
            session_match = re.search(r'/learn/session/([A-Z0-9]+)', path)
            if session_match:
                game_info['session_id'] = session_match.group(1)
        
        # Climate Game
        elif '/learn/climate/' in path or '/monsoon-mayhem/' in path:
            game_info.update({
                'game_name': 'Climate Change Challenge',
                'game_code': 'CCC001'
            })
        
        # AI Learning Games (Robotic Buddy)
        elif '/buddy/' in path or '/robotic-buddy/' in path:
            game_info.update({
                'game_name': 'Robotic Buddy AI Learning',
                'game_code': 'RBAL001'
            })
            
            # Detect specific AI game types
            if '/classification/' in path:
                game_info['game_subtype'] = 'Animal Classification'
            elif '/simple-game/' in path:
                game_info['game_subtype'] = 'Simple AI Game'
            elif '/drag-drop/' in path:
                game_info['game_subtype'] = 'Drag Drop Game'
        
        # Financial Literacy
        elif '/financial-literacy/' in path:
            game_info.update({
                'game_name': 'Financial Literacy Adventure',
                'game_code': 'FLA001'
            })
        
        # Cyber Security
        elif '/cyber-security/' in path or '/cyber-city/' in path:
            game_info.update({
                'game_name': 'Cyber Security Mission',
                'game_code': 'CSM001'
            })
        
        # Constitution Games
        elif '/constitution-basic/' in path:
            game_info.update({
                'game_name': 'Constitution Explorer Basic',
                'game_code': 'CEB001'
            })
        elif '/constitution-advanced/' in path:
            game_info.update({
                'game_name': 'Constitution Explorer Advanced',
                'game_code': 'CEA001'
            })
        
        # Entrepreneurship
        elif '/entrepreneurship/' in path:
            game_info.update({
                'game_name': 'Entrepreneurship Challenge',
                'game_code': 'EC001'
            })

        return game_info

    def get_client_ip(self, request: HttpRequest) -> str:
        """
        Get client IP address from request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'

    def track_event(self, event_name: str, properties: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """
        Track a custom event with properties
        """
        if not self.mp:
            logger.warning(f"MixPanel not initialized, cannot track event: {event_name}")
            return False
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in properties:
                properties['timestamp'] = datetime.now().isoformat()
            
            # Use provided user_id or extract from properties
            user_id = user_id or properties.get('user_id', 'unknown_user')
            
            self.mp.track(user_id, event_name, properties)
            logger.info(f"Event tracked: {event_name} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track event {event_name}: {str(e)}")
            return False

    def track_page_view(self, request: HttpRequest, page_name: str, additional_props: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track a page view from backend
        """
        properties = self.get_base_properties(request)
        properties.update({
            'page_name': page_name,
            'page_title': getattr(request, 'page_title', page_name),
            'view_source': 'backend'
        })
        
        if additional_props:
            properties.update(additional_props)
        
        return self.track_event(f'Viewed {page_name}', properties)

    def track_form_submission(self, request: HttpRequest, form_name: str, form_data: Optional[Dict[str, Any]] = None, success: bool = True) -> bool:
        """
        Track form submissions
        """
        properties = self.get_base_properties(request)
        properties.update({
            'form_name': form_name,
            'form_success': success,
            'form_method': request.method,
        })
        
        # Add sanitized form data (no PII)
        if form_data:
            sanitized_data = self.sanitize_form_data(form_data)
            properties['form_fields'] = list(sanitized_data.keys())
            properties['form_field_count'] = len(sanitized_data)
        
        event_name = 'Form Submitted' if success else 'Form Submission Failed'
        return self.track_event(event_name, properties)

    def track_game_session(self, request: HttpRequest, action: str, game_type: str, session_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track game session events (start, progress, completion)
        """
        properties = self.get_base_properties(request)
        properties.update({
            'game_type': game_type,
            'game_action': action,
        })
        
        if session_data:
            # Add relevant session data
            properties.update({
                'session_id': session_data.get('session_id'),
                'game_mode': session_data.get('game_mode'),
                'player_count': session_data.get('player_count'),
                'difficulty_level': session_data.get('difficulty_level'),
            })
        
        return self.track_event(f'Game {action}', properties)

    def track_user_content_creation(self, request: HttpRequest, content_type: str, content_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track user-generated content creation (robotic buddy, design thinking submissions)
        """
        properties = self.get_base_properties(request)
        properties.update({
            'content_type': content_type,
            'creation_timestamp': datetime.now().isoformat(),
        })
        
        if content_data:
            # Add relevant content metadata (no personal data)
            properties.update({
                'content_category': content_data.get('category'),
                'content_complexity': content_data.get('complexity'),
                'creation_time_spent': content_data.get('time_spent'),
            })
        
        return self.track_event('Content Created', properties)

    def track_error(self, request: HttpRequest, error_type: str, error_message: str, additional_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track backend errors for monitoring
        """
        properties = self.get_base_properties(request)
        properties.update({
            'error_type': error_type,
            'error_message': error_message[:500],  # Limit message length
            'error_timestamp': datetime.now().isoformat(),
        })
        
        if additional_context:
            properties.update(additional_context)
        
        return self.track_event('Backend Error', properties)

    def track_api_call(self, request: HttpRequest, endpoint: str, success: bool = True, response_time: Optional[float] = None) -> bool:
        """
        Track API endpoint usage and performance
        """
        properties = self.get_base_properties(request)
        properties.update({
            'api_endpoint': endpoint,
            'api_success': success,
            'api_method': request.method,
        })
        
        if response_time:
            properties['response_time_ms'] = response_time
        
        event_name = 'API Call Success' if success else 'API Call Failed'
        return self.track_event(event_name, properties)

    def sanitize_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove PII and sensitive data from form data before tracking
        """
        sensitive_fields = {
            'password', 'email', 'phone', 'mobile', 'address', 
            'name', 'first_name', 'last_name', 'personal_info'
        }
        
        sanitized = {}
        for key, value in form_data.items():
            if key.lower() not in sensitive_fields and 'password' not in key.lower():
                # Only track field presence and basic metadata
                sanitized[key] = 'filled' if value else 'empty'
        
        return sanitized

    def track_achievement(self, request: HttpRequest, achievement_name: str, game_type: str, achievement_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track user achievements and milestones
        """
        properties = self.get_base_properties(request)
        properties.update({
            'achievement_name': achievement_name,
            'game_type': game_type,
            'achievement_timestamp': datetime.now().isoformat(),
        })
        
        if achievement_data:
            properties.update({
                'achievement_level': achievement_data.get('level'),
                'points_earned': achievement_data.get('points'),
                'time_to_achieve': achievement_data.get('time_to_achieve'),
            })
        
        return self.track_event('Achievement Unlocked', properties)

# Global analytics instance
analytics = DecipherWorldAnalytics()

# Convenience functions for easy importing
def track_event(event_name: str, properties: Dict[str, Any], user_id: Optional[str] = None) -> bool:
    """Quick access to track_event"""
    return analytics.track_event(event_name, properties, user_id)

def track_page_view(request: HttpRequest, page_name: str, additional_props: Optional[Dict[str, Any]] = None) -> bool:
    """Quick access to track_page_view"""
    return analytics.track_page_view(request, page_name, additional_props)

def track_form_submission(request: HttpRequest, form_name: str, form_data: Optional[Dict[str, Any]] = None, success: bool = True) -> bool:
    """Quick access to track_form_submission"""
    return analytics.track_form_submission(request, form_name, form_data, success)

def track_game_session(request: HttpRequest, action: str, game_type: str, session_data: Optional[Dict[str, Any]] = None) -> bool:
    """Quick access to track_game_session"""
    return analytics.track_game_session(request, action, game_type, session_data)

def track_error(request: HttpRequest, error_type: str, error_message: str, additional_context: Optional[Dict[str, Any]] = None) -> bool:
    """Quick access to track_error"""
    return analytics.track_error(request, error_type, error_message, additional_context)

def track_user_content_creation(request: HttpRequest, content_type: str, content_data: Optional[Dict[str, Any]] = None) -> bool:
    """Quick access to track_user_content_creation"""
    return analytics.track_user_content_creation(request, content_type, content_data)