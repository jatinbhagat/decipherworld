"""
WebSocket consumers for group learning games
Real-time communication for climate game sessions
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ClimateGameSession, ClimatePlayerResponse

logger = logging.getLogger(__name__)


class ClimateGameConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for Climate Game sessions
    Handles real-time updates for facilitators and players
    """
    
    async def connect(self):
        """Accept WebSocket connection and join session group"""
        self.session_code = self.scope['url_route']['kwargs']['session_code']
        self.room_group_name = f'climate_session_{self.session_code}'
        self.user_type = None  # Will be set based on authentication
        self.connection_id = self.channel_name[-8:]  # Last 8 chars for logging
        
        # Detailed connection logging for production debugging
        logger.info(f"🔌 WebSocket CONNECT attempt - Session: {self.session_code}, Connection: {self.connection_id}")
        logger.info(f"📊 Channel Layer Backend: {self.channel_layer.__class__.__name__}")
        logger.info(f"🌐 Request Headers: {dict(self.scope.get('headers', []))}")
        logger.info(f"🔗 WebSocket Path: {self.scope.get('path', 'Unknown')}")
        
        # Validate session exists
        try:
            session_exists = await self.get_session_exists(self.session_code)
            logger.info(f"✅ Session existence check: {session_exists} for {self.session_code}")
        except Exception as e:
            logger.error(f"💥 Database error during session check: {str(e)}")
            await self.close(code=4003)
            return
            
        if not session_exists:
            logger.error(f"❌ WebSocket connection rejected: Session {self.session_code} not found (Connection: {self.connection_id})")
            await self.close(code=4004)
            return
        
        # Join room group
        try:
            logger.info(f"🔄 Attempting to join group: {self.room_group_name}")
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"✅ Successfully joined group: {self.room_group_name}")
        except Exception as e:
            logger.error(f"💥 Failed to join group {self.room_group_name}: {str(e)}")
            await self.close(code=4002)
            return
        
        try:
            await self.accept()
            logger.info(f"✅ WebSocket ACCEPTED - Session: {self.session_code}, Connection: {self.connection_id}")
        except Exception as e:
            logger.error(f"💥 Failed to accept WebSocket connection: {str(e)}")
            return
        
        # Send initial session state
        session_data = await self.get_session_status(self.session_code)
        await self.send(text_data=json.dumps({
            'type': 'session_status',
            'data': session_data
        }))
        
        logger.info(f"📊 WebSocket sent initial status - Session: {self.session_code}, Phase: {session_data.get('current_phase') if session_data else 'None'}, Connection: {self.connection_id}")

    async def disconnect(self, close_code):
        """Leave session group when disconnecting"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Log disconnect with detailed reason
        disconnect_reason = self.get_disconnect_reason(close_code)
        logger.warning(f"🔌 WebSocket DISCONNECT - Session: {self.session_code}, Code: {close_code} ({disconnect_reason}), User: {self.user_type}, Connection: {self.connection_id}")

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Respond to ping with pong for connection health check
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
                
            elif message_type == 'join_as_facilitator':
                self.user_type = 'facilitator'
                await self.send(text_data=json.dumps({
                    'type': 'joined',
                    'role': 'facilitator'
                }))
                
            elif message_type == 'join_as_player':
                self.user_type = 'player'
                player_name = data.get('player_name', 'Anonymous')
                await self.send(text_data=json.dumps({
                    'type': 'joined',
                    'role': 'player',
                    'player_name': player_name
                }))
                
            elif message_type == 'request_status':
                # Send current session status
                session_data = await self.get_session_status(self.session_code)
                await self.send(text_data=json.dumps({
                    'type': 'session_status',
                    'data': session_data
                }))
                
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")

    async def session_update(self, event):
        """Send session update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'session_update',
            'data': event['data']
        }))

    async def game_event(self, event):
        """Send game event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'game_event',
            'event_type': event['event_type'],
            'data': event['data']
        }))

    async def player_joined(self, event):
        """Notify about new player joining"""
        await self.send(text_data=json.dumps({
            'type': 'player_joined',
            'player_name': event['player_name'],
            'total_players': event['total_players']
        }))

    async def phase_changed(self, event):
        """Notify about game phase change"""
        logger.info(f"🎯 Broadcasting phase_changed to {self.session_code} - Phase: {event['new_phase']}, Round: {event['current_round']}, Connection: {self.connection_id}")
        await self.send(text_data=json.dumps({
            'type': 'phase_changed',
            'new_phase': event['new_phase'],
            'current_round': event['current_round']
        }))
        logger.info(f"📨 Sent phase_changed message to connection: {self.connection_id}")

    async def response_received(self, event):
        """Notify about new player response"""
        await self.send(text_data=json.dumps({
            'type': 'response_received',
            'responses_count': event['responses_count'],
            'total_players': event['total_players']
        }))

    async def error_notification(self, event):
        """Send error notification"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': event['message']
        }))

    async def timer_started(self, event):
        """Handle timer started notification"""
        logger.info(f"🕐 Broadcasting timer_started to {self.session_code} - Connection: {self.connection_id}")
        await self.send(text_data=json.dumps({
            'type': 'timer_started',
            'duration': event.get('duration'),
            'end_time': event.get('end_time'),
            'timer_info': event.get('timer_info', {})
        }))

    async def timer_update(self, event):
        """Handle timer update notification"""
        logger.info(f"🕐 Broadcasting timer_update to {self.session_code} - Connection: {self.connection_id}")
        await self.send(text_data=json.dumps({
            'type': 'timer_update',
            'end_time': event.get('end_time'),
            'timer_info': event.get('timer_info', {}),
            'remaining_time': event.get('remaining_time')
        }))

    # Database helper methods
    @database_sync_to_async
    def get_session_exists(self, session_code):
        """Check if session exists"""
        return ClimateGameSession.objects.filter(session_code=session_code).exists()

    @database_sync_to_async
    def get_session_status(self, session_code):
        """Get current session status"""
        try:
            session = ClimateGameSession.objects.get(session_code=session_code)
            
            # Count responses for current round
            current_responses = ClimatePlayerResponse.objects.filter(
                climate_session=session,
                round_number=session.current_round
            ).count()
            
            # Count total unique players
            total_players = ClimatePlayerResponse.objects.filter(
                climate_session=session
            ).values('player_session_id').distinct().count()
            
            # Get actual student list with roles
            students_data = []
            unique_players = ClimatePlayerResponse.objects.filter(
                climate_session=session
            ).values('player_session_id', 'assigned_role', 'player_name').distinct()
            
            for player in unique_players:
                students_data.append({
                    'player_session_id': player['player_session_id'],
                    'role': player['assigned_role'],
                    'player_name': player['player_name'] or player['player_session_id']  # Use actual name or fallback to session ID
                })
            
            return {
                'status': session.status,
                'current_phase': session.current_phase,
                'current_round': session.current_round,
                'responses_count': current_responses,
                'total_players': total_players,
                'students': students_data,  # Add actual student list
                'session_name': f"Test Session - {session.session_code}",
                'facilitator_name': session.facilitator.username if session.facilitator else "Developer",
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'environment_health': getattr(session, 'environment_health', 50),
                'economy_health': getattr(session, 'economy_health', 50),
                'social_equity': getattr(session, 'social_equity', 50),
            }
        except ClimateGameSession.DoesNotExist:
            return None

    def get_disconnect_reason(self, close_code):
        """Get human-readable disconnect reason"""
        reasons = {
            1000: "Normal closure",
            1001: "Going away (page reload/navigation)", 
            1002: "Protocol error",
            1003: "Unsupported data",
            1006: "Abnormal closure (no close frame)",
            1011: "Internal server error",
            1012: "Service restart",
            1013: "Try again later",
            1014: "Bad gateway",
            1015: "TLS handshake failure",
            4004: "Session not found"
        }
        return reasons.get(close_code, f"Unknown code {close_code}")


# ClimateGameLobbyConsumer removed - Using unified ClimateGameConsumer for all phases
# This eliminates dual WebSocket architecture and prevents race conditions