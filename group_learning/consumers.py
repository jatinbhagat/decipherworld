"""
WebSocket consumers for group learning games
Real-time communication for climate game sessions
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from .models import (
    ClimateGameSession, ClimatePlayerResponse,
    DesignThinkingSession, DesignTeam, TeamSubmission, TeamProgress
)

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


class DesignThinkingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for Design Thinking sessions
    Handles real-time updates for facilitators and teams
    """
    
    async def connect(self):
        """Accept WebSocket connection and join session group"""
        self.session_code = self.scope['url_route']['kwargs']['session_code']
        self.room_group_name = f'design_thinking_{self.session_code}'
        self.user_type = None  # facilitator or team
        self.team_id = None  # Will be set for team connections
        self.connection_id = self.channel_name[-8:]
        
        logger.info(f"🎨 Design Thinking WebSocket CONNECT - Session: {self.session_code}, Connection: {self.connection_id}")
        
        # Validate session exists
        try:
            session_exists = await self.get_design_session_exists(self.session_code)
            logger.info(f"✅ Design session existence check: {session_exists} for {self.session_code}")
        except Exception as e:
            logger.error(f"💥 Database error during design session check: {str(e)}")
            await self.close(code=4003)
            return
            
        if not session_exists:
            logger.error(f"❌ Design Thinking connection rejected: Session {self.session_code} not found")
            await self.close(code=4004)
            return
        
        # Join room group
        try:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"✅ Design Thinking WebSocket CONNECTED - Session: {self.session_code}, Group: {self.room_group_name}")
            
            # Send initial session status
            session_status = await self.get_design_session_status(self.session_code)
            await self.send(text_data=json.dumps({
                'type': 'session_status',
                'data': session_status
            }))
            
        except Exception as e:
            logger.error(f"💥 Failed to join Design Thinking group {self.room_group_name}: {str(e)}")
            await self.close(code=4003)

    async def disconnect(self, close_code):
        """Leave room group"""
        logger.info(f"🔌 Design Thinking WebSocket DISCONNECT - Session: {self.session_code}, Code: {close_code} ({self.get_close_reason(close_code)})")
        
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception as e:
            logger.error(f"💥 Error leaving Design Thinking group {self.room_group_name}: {str(e)}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            logger.info(f"📨 Design Thinking WebSocket message received - Type: {message_type}, Session: {self.session_code}")
            
            if message_type == 'mission_control':
                await self.handle_mission_control(data)
            elif message_type == 'team_update':
                await self.handle_team_update(data)
            elif message_type == 'vani_nudge':
                await self.handle_vani_nudge(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                logger.warning(f"⚠️ Unknown Design Thinking message type: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"💥 Invalid JSON in Design Thinking WebSocket message: {str(e)}")
        except Exception as e:
            logger.error(f"💥 Error processing Design Thinking WebSocket message: {str(e)}")

    async def handle_mission_control(self, data):
        """Handle facilitator mission control actions"""
        action = data.get('action')
        
        if action == 'advance_mission':
            mission_id = data.get('mission_id')
            await self.advance_mission(mission_id)
        elif action == 'spotlight_team':
            team_id = data.get('team_id')
            await self.spotlight_team(team_id)
        elif action == 'send_nudge':
            nudge_data = data.get('nudge_data')
            await self.send_vani_nudge(nudge_data)

    async def handle_team_update(self, data):
        """Handle team progress updates"""
        team_id = data.get('team_id')
        update_type = data.get('update_type')
        
        if update_type == 'submission':
            await self.broadcast_team_submission(team_id, data.get('submission_data'))
        elif update_type == 'progress':
            await self.broadcast_team_progress(team_id, data.get('progress_data'))

    async def handle_vani_nudge(self, data):
        """Handle Vani mentor nudge requests"""
        await self.send_group_message('vani_nudge', data.get('nudge_data'))

    # Group message handlers
    async def mission_advanced(self, event):
        """Send mission advancement to client"""
        await self.send(text_data=json.dumps({
            'type': 'mission_advanced',
            'mission_data': event['mission_data'],
            'timestamp': event.get('timestamp')
        }))

    async def team_submission_update(self, event):
        """Send team submission update to client"""
        await self.send(text_data=json.dumps({
            'type': 'team_submission',
            'team_data': event['team_data'],
            'submission_data': event['submission_data'],
            'timestamp': event.get('timestamp')
        }))

    async def team_progress_update(self, event):
        """Send team progress update to client"""
        await self.send(text_data=json.dumps({
            'type': 'team_progress',
            'team_data': event['team_data'],
            'progress_data': event['progress_data'],
            'timestamp': event.get('timestamp')
        }))

    async def team_spotlight(self, event):
        """Send team spotlight notification to client"""
        await self.send(text_data=json.dumps({
            'type': 'team_spotlight',
            'team_data': event['team_data'],
            'spotlight_reason': event.get('spotlight_reason'),
            'timestamp': event.get('timestamp')
        }))

    async def vani_nudge(self, event):
        """Send Vani mentor nudge to client"""
        await self.send(text_data=json.dumps({
            'type': 'vani_nudge',
            'nudge_data': event['nudge_data'],
            'timestamp': event.get('timestamp')
        }))

    async def session_status_update(self, event):
        """Send session status update to client"""
        await self.send(text_data=json.dumps({
            'type': 'session_status',
            'data': event['session_data'],
            'timestamp': event.get('timestamp')
        }))

    async def team_joined(self, event):
        """Send team joined notification to client"""
        await self.send(text_data=json.dumps({
            'type': 'team_joined',
            'team_data': event['team_data'],
            'session_data': event['session_data'],
            'timestamp': event.get('timestamp')
        }))

    # Helper methods for group messaging
    async def send_group_message(self, message_type, data):
        """Send message to all clients in the session group"""
        from django.utils import timezone
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': message_type,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def advance_mission(self, mission_id):
        """Advance session to specified mission"""
        try:
            mission_data = await self.set_current_mission(self.session_code, mission_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'mission_advanced',
                    'mission_data': mission_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error advancing mission: {str(e)}")

    async def broadcast_team_submission(self, team_id, submission_data):
        """Broadcast team submission to all session participants"""
        try:
            team_data = await self.get_team_data(team_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'team_submission_update',
                    'team_data': team_data,
                    'submission_data': submission_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting team submission: {str(e)}")

    async def broadcast_team_progress(self, team_id, progress_data):
        """Broadcast team progress to all session participants"""
        try:
            team_data = await self.get_team_data(team_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'team_progress_update',
                    'team_data': team_data,
                    'progress_data': progress_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting team progress: {str(e)}")

    async def spotlight_team(self, team_id):
        """Spotlight a team for exceptional work"""
        try:
            team_data = await self.get_team_data(team_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'team_spotlight',
                    'team_data': team_data,
                    'spotlight_reason': 'Facilitator highlight',
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error spotlighting team: {str(e)}")

    async def send_vani_nudge(self, nudge_data):
        """Send Vani mentor nudge to all teams"""
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'vani_nudge',
                    'nudge_data': nudge_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error sending Vani nudge: {str(e)}")

    # Database helper methods
    @database_sync_to_async
    def get_design_session_exists(self, session_code):
        """Check if Design Thinking session exists"""
        return DesignThinkingSession.objects.filter(session_code=session_code).exists()

    @database_sync_to_async
    def get_design_session_status(self, session_code):
        """Get current Design Thinking session status"""
        try:
            session = DesignThinkingSession.objects.select_related('current_mission').get(session_code=session_code)
            
            # Get teams and their progress
            teams_data = []
            try:
                for team in session.design_teams.all():
                    teams_data.append({
                        'id': team.id,
                        'name': team.team_name,
                        'emoji': team.team_emoji,
                        'color': team.team_color,
                        'missions_completed': getattr(team, 'missions_completed', 0),
                        'total_submissions': getattr(team, 'total_submissions', 0),
                        'progress_percentage': getattr(team, 'get_progress_percentage', lambda: 0)()
                    })
            except Exception as e:
                logger.error(f"Error processing teams data: {str(e)}")
                teams_data = []
            
            # Get mission progress safely
            mission_progress = {'completed': 0, 'total': 0, 'percentage': 0}
            try:
                mission_progress = session.get_mission_progress()
            except Exception as e:
                logger.error(f"Error getting mission progress: {str(e)}")
            
            return {
                'status': session.status,
                'current_mission': {
                    'id': session.current_mission.id,
                    'title': session.current_mission.title,
                    'mission_type': session.current_mission.mission_type,
                    'description': session.current_mission.description
                } if session.current_mission else None,
                'teams': teams_data,
                'teams_count': len(teams_data),
                'mission_progress': mission_progress,
                'session_started': session.started_at.isoformat() if session.started_at else None,
                'mission_started': session.mission_start_time.isoformat() if session.mission_start_time else None
            }
            
        except DesignThinkingSession.DoesNotExist:
            logger.warning(f"Session not found: {session_code}")
            return {'error': 'Session not found'}
        except Exception as e:
            logger.error(f"Error getting design session status for {session_code}: {str(e)}")
            return {'error': 'Status retrieval failed'}

    @database_sync_to_async
    def set_current_mission(self, session_code, mission_id):
        """Set current mission for the session"""
        try:
            from .models import DesignMission
            
            session = DesignThinkingSession.objects.get(session_code=session_code)
            mission = DesignMission.objects.get(id=mission_id, game=session.design_game)
            
            session.current_mission = mission
            session.mission_start_time = timezone.now()
            session.save()
            
            return {
                'id': mission.id,
                'title': mission.title,
                'mission_type': mission.mission_type,
                'description': getattr(mission, 'description', ''),
                'instructions': getattr(mission, 'instructions', '')
            }
            
        except DesignThinkingSession.DoesNotExist:
            logger.error(f"Session not found when setting mission: {session_code}")
            raise Exception(f"Session {session_code} not found")
        except Exception as e:
            logger.error(f"Error setting current mission {mission_id} for session {session_code}: {str(e)}")
            raise e

    @database_sync_to_async
    def get_team_data(self, team_id):
        """Get team data for broadcasting"""
        try:
            team = DesignTeam.objects.get(id=team_id)
            return {
                'id': team.id,
                'name': team.team_name,
                'emoji': team.team_emoji,
                'color': getattr(team, 'team_color', '#3B82F6'),
                'missions_completed': getattr(team, 'missions_completed', 0),
                'total_submissions': getattr(team, 'total_submissions', 0)
            }
        except DesignTeam.DoesNotExist:
            logger.warning(f"Team not found: {team_id}")
            return {'error': 'Team not found'}
        except Exception as e:
            logger.error(f"Error getting team data for team {team_id}: {str(e)}")
            return {'error': 'Team data retrieval failed'}

    def get_close_reason(self, close_code):
        """Get human-readable close reason"""
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
            4003: "Database error",
            4004: "Session not found"
        }
        return reasons.get(close_code, f"Unknown code {close_code}")