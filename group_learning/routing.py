"""
WebSocket URL routing for group learning games
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Climate Game WebSocket endpoints - Unified consumer for all phases
    re_path(r'ws/climate/(?P<session_code>\w+)/$', consumers.ClimateGameConsumer.as_asgi()),
    # Legacy lobby endpoint redirects to main consumer for backward compatibility  
    re_path(r'ws/climate-lobby/(?P<session_code>\w+)/$', consumers.ClimateGameConsumer.as_asgi()),
    
    # Design Thinking WebSocket endpoints
    re_path(r'ws/design-thinking/(?P<session_code>\w+)/$', consumers.DesignThinkingConsumer.as_asgi()),
]