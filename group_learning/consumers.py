"""
WebSocket consumers for group learning games
Real-time communication for climate game sessions
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.conf import settings
from .models import (
    ClimateGameSession, ClimatePlayerResponse,
    DesignThinkingSession, DesignTeam, DesignMission, TeamSubmission, TeamProgress
)
from .monitoring import log_websocket_event

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
        self.last_ping = timezone.now()
        self.ping_task = None
        self.connection_timeout = getattr(settings, 'WEBSOCKET_TIMEOUT', 60)  # 1 minute default
        
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
            
            # Start ping monitoring task
            self.ping_task = asyncio.create_task(self.ping_monitor())
            
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
        # Cancel ping monitoring task
        if self.ping_task and not self.ping_task.done():
            self.ping_task.cancel()
            try:
                await self.ping_task
            except asyncio.CancelledError:
                pass
        
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
                # Update last ping time and respond
                self.last_ping = timezone.now()
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
                
            elif message_type == 'join_as_student':
                self.user_type = 'student'
                team_id = data.get('team_id')
                student_data = data.get('student_data', {})
                await self.send(text_data=json.dumps({
                    'type': 'joined',
                    'role': 'student',
                    'team_id': team_id
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
            4004: "Session not found",
            4005: "Connection timeout"
        }
        return reasons.get(close_code, f"Unknown code {close_code}")

    async def ping_monitor(self):
        """Monitor connection health and close if inactive"""
        try:
            while True:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                time_since_ping = timezone.now() - self.last_ping
                if time_since_ping.total_seconds() > self.connection_timeout:
                    logger.warning(f"⏰ Connection timeout - Session: {self.session_code}, Connection: {self.connection_id}, Last ping: {time_since_ping.total_seconds()}s ago")
                    await self.close(code=4005)  # Custom timeout code
                    break
                    
        except asyncio.CancelledError:
            logger.info(f"🔄 Ping monitor cancelled for connection: {self.connection_id}")
        except Exception as e:
            logger.error(f"💥 Error in ping monitor for connection {self.connection_id}: {str(e)}")


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
        self.last_ping = timezone.now()
        self.ping_task = None
        self.connection_timeout = getattr(settings, 'WEBSOCKET_TIMEOUT', 60)
        
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
            
            # Log connection event
            log_websocket_event(
                self.session_code, 
                'connect', 
                self.connection_id,
                {'room_group': self.room_group_name}
            )
            
            # Start ping monitoring task
            self.ping_task = asyncio.create_task(self.design_ping_monitor())
            
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
        # Cancel ping monitoring task
        if self.ping_task and not self.ping_task.done():
            self.ping_task.cancel()
            try:
                await self.ping_task
            except asyncio.CancelledError:
                pass
        
        disconnect_reason = self.get_close_reason(close_code)
        logger.info(f"🔌 Design Thinking WebSocket DISCONNECT - Session: {self.session_code}, Code: {close_code} ({disconnect_reason})")
        
        # Log disconnection event
        log_websocket_event(
            self.session_code,
            'disconnect',
            self.connection_id,
            {
                'close_code': close_code,
                'close_reason': disconnect_reason,
                'user_type': getattr(self, 'user_type', 'unknown')
            }
        )
        
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
            elif message_type == 'simplified_input_submit':
                await self.handle_simplified_input(data)
            elif message_type == 'teacher_score_submit':
                await self.handle_teacher_scoring(data)
            elif message_type == 'teacher_feedback_submit':
                await self.handle_teacher_feedback(data)
            elif message_type == 'vani_nudge':
                await self.handle_vani_nudge(data)
            elif message_type == 'ping':
                self.last_ping = timezone.now()
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp'),
                    'server_time': timezone.now().isoformat(),
                    'connection_id': self.connection_id
                }))
            elif message_type == 'join_as_facilitator':
                self.user_type = 'facilitator'
                await self.send(text_data=json.dumps({
                    'type': 'joined',
                    'role': 'facilitator'
                }))
            elif message_type == 'join_as_student':
                self.user_type = 'student'
                team_id = data.get('team_id')
                student_data = data.get('student_data', {})
                await self.send(text_data=json.dumps({
                    'type': 'joined',
                    'role': 'student',
                    'team_id': team_id
                }))
            elif message_type == 'heartbeat_response':
                # Client responded to heartbeat
                self.last_ping = timezone.now()
            elif message_type == 'reconnect_request':
                # Client is requesting reconnection
                await self.handle_reconnection_request(data)
            elif message_type == 'connection_status':
                # Client requesting connection status
                await self.send_connection_status()
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

    async def handle_simplified_input(self, data):
        """Handle simplified phase input submission with auto-progression logic"""
        try:
            # Validate required fields
            team_id = data.get('team_id')
            mission_id = data.get('mission_id')
            student_data = data.get('student_data')
            input_data = data.get('input_data')
            
            if not all([team_id, mission_id, student_data, input_data]):
                await self.send_error('Missing required fields for input submission')
                return
            
            # Rate limiting check
            if not await self.check_rate_limit(team_id):
                await self.send_error('Too many submissions. Please wait before trying again.')
                return
            
            # Process through auto-progression service
            from .auto_progression_service import auto_progression_service
            
            result = await self.run_in_executor(
                auto_progression_service.process_phase_input,
                team_id, mission_id, student_data, input_data
            )
            
            if result.get('success'):
                # Send success confirmation to submitter
                await self.send(text_data=json.dumps({
                    'type': 'input_submission_success',
                    'phase_input_id': result.get('phase_input_id'),
                    'completion_result': result.get('completion_result'),
                    'progression_result': result.get('progression_result'),
                    'timestamp': timezone.now().isoformat()
                }))
                
                # Broadcast submission to teacher dashboard for real-time review
                await self.broadcast_submission_to_teachers(result, team_id, mission_id, student_data, input_data)
                
                # Handle auto-advancement if triggered
                progression_result = result.get('progression_result', {})
                if progression_result.get('should_advance'):
                    await self.handle_auto_advancement(progression_result)
                    
            else:
                error_msg = result.get('error', 'Unknown error occurred')
                retry_allowed = result.get('retry_allowed', False)
                await self.send_error(error_msg, retry_allowed)
                
        except Exception as e:
            logger.error(f"Unexpected error handling simplified input: {str(e)}", exc_info=True)
            await self.send_error('Internal server error. Please try again later.', retry_allowed=True)

    async def handle_teacher_scoring(self, data):
        """Handle teacher scoring of team submissions"""
        try:
            team_id = data.get('team_id')
            mission_id = data.get('mission_id')
            score = data.get('score')
            teacher_id = data.get('teacher_id')
            
            # Save teacher score
            score_saved = await self.save_teacher_score(team_id, mission_id, score, teacher_id)
            
            if score_saved:
                # Broadcast score update to dashboard
                await self.broadcast_score_update(team_id, mission_id, score)
                
        except Exception as e:
            logger.error(f"Error handling teacher scoring: {str(e)}")
            await self.send_error('Failed to save teacher score')

    async def handle_teacher_feedback(self, data):
        """Handle real-time teacher feedback submission"""
        try:
            team_id = data.get('team_id')
            submission_id = data.get('submission_id')
            message = data.get('message', '').strip()
            score = data.get('score')
            feedback_type = data.get('feedback_type', 'teacher_message')
            sender_name = data.get('sender_name', 'Teacher')
            
            # Validation
            if not team_id:
                await self.send_error('Team ID is required for feedback')
                return
                
            if not message and not score:
                await self.send_error('Either message or score is required')
                return
            
            # Create feedback record
            feedback_created = await self.create_feedback_record(
                team_id, submission_id, message, score, feedback_type, sender_name
            )
            
            if feedback_created:
                # Broadcast feedback to students in real-time
                await self.broadcast_teacher_feedback(feedback_created)
                
                # Send success confirmation to teacher
                await self.send(text_data=json.dumps({
                    'type': 'feedback_submission_success',
                    'feedback_id': feedback_created['id'],
                    'team_id': team_id,
                    'timestamp': timezone.now().isoformat()
                }))
                
        except Exception as e:
            logger.error(f"Error handling teacher feedback: {str(e)}")
            await self.send_error('Failed to save teacher feedback')

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

    async def input_submission_update(self, event):
        """Send simplified input submission update to client"""
        await self.send(text_data=json.dumps({
            'type': 'input_submission',
            'team_data': event['team_data'],
            'input_data': event['input_data'],
            'auto_advance_result': event.get('auto_advance_result'),
            'timestamp': event.get('timestamp')
        }))

    async def teacher_feedback_update(self, event):
        """Send teacher feedback update to client"""
        await self.send(text_data=json.dumps({
            'type': 'teacher_feedback',
            'feedback_data': event['feedback_data'],
            'team_data': event.get('team_data'),
            'timestamp': event.get('timestamp')
        }))

    async def student_submission_for_review(self, event):
        """Send student submission to teacher dashboard for review"""
        await self.send(text_data=json.dumps({
            'type': 'submission_for_review',
            'submission_data': event['submission_data'],
            'team_data': event.get('team_data'),
            'timestamp': event.get('timestamp')
        }))

    async def phase_auto_advance(self, event):
        """Send auto-advancement notification to client"""
        await self.send(text_data=json.dumps({
            'type': 'phase_auto_advance',
            'current_mission': event['current_mission'],
            'next_mission': event['next_mission'],
            'countdown_seconds': event.get('countdown_seconds', 3),
            'timestamp': event.get('timestamp')
        }))

    async def teacher_score_update(self, event):
        """Send teacher score update to client"""
        await self.send(text_data=json.dumps({
            'type': 'teacher_score',
            'team_data': event['team_data'],
            'mission_data': event['mission_data'],
            'score': event['score'],
            'timestamp': event.get('timestamp')
        }))

    async def completion_status_update(self, event):
        """Send team completion status update to client"""
        await self.send(text_data=json.dumps({
            'type': 'completion_status',
            'team_data': event['team_data'],
            'completion_percentage': event['completion_percentage'],
            'is_ready_to_advance': event['is_ready_to_advance'],
            'timestamp': event.get('timestamp')
        }))

    async def rating_updated(self, event):
        """Send rating update to teacher dashboard"""
        await self.send(text_data=json.dumps({
            'type': 'rating_updated',
            'team_id': event['team_id'],
            'team_name': event['team_name'],
            'mission_type': event['mission_type'],
            'rating': event['rating'],
            'rating_stars': event['rating_stars'],
            'feedback': event['feedback'],
            'average_rating': event['average_rating'],
            'timestamp': event['timestamp']
        }))

    async def submission_scored_update(self, event):
        """Send submission scored update to all clients (real-time score updates)"""
        await self.send(text_data=json.dumps({
            'type': 'submission_scored',
            'submission': event['submission_data'],
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

    async def broadcast_input_submission(self, team_id, mission_id, input_data, auto_advance_result):
        """Broadcast simplified input submission to all session participants"""
        try:
            team_data = await self.get_team_data(team_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'input_submission_update',
                    'team_data': team_data,
                    'input_data': input_data,
                    'auto_advance_result': auto_advance_result,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting input submission: {str(e)}")

    async def broadcast_score_update(self, team_id, mission_id, score):
        """Broadcast teacher score update to dashboard"""
        try:
            team_data = await self.get_team_data(team_id)
            mission_data = await self.get_mission_data(mission_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'teacher_score_update',
                    'team_data': team_data,
                    'mission_data': mission_data,
                    'score': score,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting score update: {str(e)}")

    async def handle_auto_advancement(self, auto_advance_result):
        """Handle auto-advancement to next phase with countdown"""
        try:
            current_mission = auto_advance_result['current_mission']
            next_mission = auto_advance_result['next_mission']
            countdown_seconds = auto_advance_result.get('countdown_seconds', 3)
            
            # Broadcast auto-advance notification
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'phase_auto_advance',
                    'current_mission': current_mission,
                    'next_mission': next_mission,
                    'countdown_seconds': countdown_seconds,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Wait for countdown, then advance
            import asyncio
            await asyncio.sleep(countdown_seconds)
            
            # Actually advance the session
            mission_data = await self.set_current_mission(self.session_code, next_mission['id'])
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'mission_advanced',
                    'mission_data': mission_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling auto-advancement: {str(e)}")

    async def send_error(self, message, retry_allowed=False, error_code=None):
        """Send error message to client with enhanced details"""
        error_response = {
            'type': 'error',
            'message': message,
            'retry_allowed': retry_allowed,
            'timestamp': timezone.now().isoformat(),
            'connection_id': getattr(self, 'connection_id', 'unknown')
        }
        
        if error_code:
            error_response['error_code'] = error_code
            
        await self.send(text_data=json.dumps(error_response))
        logger.warning(f"🚨 Sent error to client: {message} (retry_allowed: {retry_allowed})")
    
    async def check_rate_limit(self, team_id):
        """Check if team is within rate limits for submissions"""
        try:
            # Simple rate limiting: max 10 submissions per minute per team
            from django.core.cache import cache
            cache_key = f'rate_limit_team_{team_id}'
            current_time = timezone.now()
            
            # Get submission count from last minute
            submission_count = cache.get(cache_key, 0)
            
            if submission_count >= 10:
                logger.warning(f"⚠️ Rate limit exceeded for team {team_id}: {submission_count} submissions")
                return False
            
            # Increment counter with 60-second expiry
            cache.set(cache_key, submission_count + 1, 60)
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return True  # Allow on error to avoid blocking legitimate requests
    
    async def design_ping_monitor(self):
        """Monitor connection health with ping/pong and automatic reconnection"""
        try:
            heartbeat_interval = 15  # Send heartbeat every 15 seconds
            timeout_threshold = 60   # Timeout after 60 seconds of no response
            
            while True:
                await asyncio.sleep(heartbeat_interval)
                
                # Send heartbeat to client
                try:
                    await self.send(text_data=json.dumps({
                        'type': 'heartbeat',
                        'timestamp': timezone.now().isoformat(),
                        'connection_id': self.connection_id
                    }))
                except Exception as e:
                    logger.error(f"💥 Failed to send heartbeat: {str(e)}")
                    break
                
                # Check for timeout
                time_since_ping = timezone.now() - self.last_ping
                if time_since_ping.total_seconds() > timeout_threshold:
                    logger.warning(f"🔌 Design Thinking connection timeout - Session: {self.session_code}, Last ping: {time_since_ping.total_seconds()}s ago")
                    
                    # Attempt graceful reconnection
                    await self.send(text_data=json.dumps({
                        'type': 'connection_timeout',
                        'message': 'Connection timeout detected. Please refresh to reconnect.',
                        'should_reconnect': True,
                        'timeout_seconds': time_since_ping.total_seconds()
                    }))
                    
                    await asyncio.sleep(5)  # Give client time to receive message
                    await self.close(code=4001)
                    break
                    
        except asyncio.CancelledError:
            logger.info(f"🔌 Design Thinking ping monitor cancelled - Session: {self.session_code}")
        except Exception as e:
            logger.error(f"💥 Error in Design Thinking ping monitor: {str(e)}")
    
    def get_close_reason(self, close_code):
        """Get human-readable close reason"""
        close_reasons = {
            1000: 'Normal closure',
            1001: 'Going away',
            1002: 'Protocol error',
            1003: 'Unsupported data',
            1006: 'Abnormal closure',
            4001: 'Connection timeout',
            4002: 'Failed to join group',
            4003: 'Database error',
            4004: 'Session not found',
            4005: 'Connection recovery failed',
            4006: 'Rate limit exceeded'
        }
        return close_reasons.get(close_code, f'Unknown ({close_code})')
    
    async def run_in_executor(self, func, *args):
        """Run synchronous function in thread executor"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, func, *args)
    
    # Database helper methods (async wrappers)
    @database_sync_to_async
    def get_design_session_exists(self, session_code):
        """Check if design thinking session exists"""
        try:
            return DesignThinkingSession.objects.filter(session_code=session_code).exists()
        except Exception as e:
            logger.error(f"Error checking design session existence: {str(e)}")
            return False
    
    @database_sync_to_async
    def get_design_session_status(self, session_code):
        """Get current design thinking session status"""
        try:
            session = DesignThinkingSession.objects.select_related('design_game', 'current_mission').get(session_code=session_code)
            
            # Get teams with member counts
            teams_data = []
            for team in session.design_teams.all():
                team_members = team.team_members or []
                teams_data.append({
                    'id': team.id,
                    'name': team.team_name,
                    'emoji': team.team_emoji,
                    'member_count': len(team_members),
                    'members': team_members
                })
            
            # Get current mission data
            current_mission_data = None
            if session.current_mission:
                current_mission_data = {
                    'id': session.current_mission.id,
                    'title': session.current_mission.title,
                    'description': session.current_mission.description,
                    'mission_type': session.current_mission.mission_type,
                    'order': session.current_mission.order
                }
            
            return {
                'session_code': session.session_code,
                'session_name': session.session_name,
                'game_name': session.design_game.name,
                'current_mission': current_mission_data,
                'teams': teams_data,
                'total_teams': len(teams_data),
                'is_active': session.is_active,
                'auto_advance_enabled': session.design_game.auto_advance_enabled,
                'completion_threshold': session.design_game.completion_threshold_percentage
            }
            
        except DesignThinkingSession.DoesNotExist:
            logger.error(f"Design thinking session {session_code} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting design session status: {str(e)}")
            return None
    
    @database_sync_to_async
    def get_team_data(self, team_id):
        """Get team data for broadcasting"""
        try:
            team = DesignTeam.objects.get(id=team_id)
            return {
                'id': team.id,
                'name': team.team_name,
                'emoji': team.team_emoji,
                'member_count': len(team.team_members or [])
            }
        except DesignTeam.DoesNotExist:
            logger.error(f"Team {team_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting team data: {str(e)}")
            return None
    
    @database_sync_to_async
    def get_mission_data(self, mission_id):
        """Get mission data for broadcasting"""
        try:
            mission = DesignMission.objects.get(id=mission_id)
            return {
                'id': mission.id,
                'title': mission.title,
                'mission_type': mission.mission_type,
                'description': mission.description
            }
        except DesignMission.DoesNotExist:
            logger.error(f"Mission {mission_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting mission data: {str(e)}")
            return None
    
    @database_sync_to_async
    def set_current_mission(self, session_code, mission_id):
        """Set current mission for session"""
        try:
            session = DesignThinkingSession.objects.get(session_code=session_code)
            mission = DesignMission.objects.get(id=mission_id)
            
            session.current_mission = mission
            session.mission_start_time = timezone.now()
            session.save()
            
            return {
                'id': mission.id,
                'title': mission.title,
                'description': mission.description,
                'mission_type': mission.mission_type,
                'order': mission.order
            }
            
        except (DesignThinkingSession.DoesNotExist, DesignMission.DoesNotExist) as e:
            logger.error(f"Error setting current mission: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error setting current mission: {str(e)}")
            return None
    
    @database_sync_to_async
    def save_teacher_score(self, team_id, mission_id, score, teacher_id):
        """Save teacher score for team's mission performance"""
        try:
            from .auto_progression_service import auto_progression_service
            return auto_progression_service.save_teacher_score(team_id, mission_id, score, teacher_id)
        except Exception as e:
            logger.error(f"Error saving teacher score: {str(e)}")
            return False
    
    async def handle_reconnection_request(self, data):
        """Handle client reconnection request"""
        try:
            client_session_id = data.get('client_session_id')
            last_known_state = data.get('last_known_state', {})
            
            logger.info(f"🔄 Reconnection request from client {client_session_id} - Session: {self.session_code}")
            
            # Send current session state to reconnecting client
            session_status = await self.get_design_session_status(self.session_code)
            
            await self.send(text_data=json.dumps({
                'type': 'reconnection_complete',
                'session_status': session_status,
                'server_time': timezone.now().isoformat(),
                'message': 'Successfully reconnected to session'
            }))
            
            # Log reconnection event
            log_websocket_event(
                self.session_code,
                'reconnection_completed',
                self.connection_id,
                {
                    'client_session_id': client_session_id,
                    'had_previous_state': bool(last_known_state)
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling reconnection request: {str(e)}")
            await self.send_error('Failed to complete reconnection', error_code='RECONNECTION_ERROR')
    
    async def send_connection_status(self):
        """Send current connection status to client"""
        try:
            connection_stats = {
                'connection_id': self.connection_id,
                'session_code': self.session_code,
                'connected_at': timezone.now().isoformat(),
                'last_ping': self.last_ping.isoformat() if self.last_ping else None,
                'user_type': getattr(self, 'user_type', 'unknown'),
                'room_group': self.room_group_name
            }
            
            await self.send(text_data=json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'connection_stats': connection_stats,
                'server_time': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error sending connection status: {str(e)}")
    
    async def handle_connection_recovery(self):
        """Handle connection recovery scenarios"""
        try:
            # Check if session is still valid
            session_exists = await self.get_design_session_exists(self.session_code)
            
            if not session_exists:
                await self.send(text_data=json.dumps({
                    'type': 'session_expired',
                    'message': 'This session is no longer available',
                    'should_redirect': True,
                    'redirect_url': '/learn/design-thinking/'
                }))
                await self.close(code=4004)
                return
            
            # Send recovery confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_recovered',
                'message': 'Connection has been recovered',
                'session_code': self.session_code,
                'server_time': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error in connection recovery: {str(e)}")
            await self.close(code=4003)
            
            # For now, always allow (can be enhanced with Redis cache)
            return True
            
        except Exception as e:
            logger.warning(f"Rate limit check failed: {str(e)}")
            return True  # Allow on error to not block legitimate requests
    
    async def run_in_executor(self, func, *args):
        """Run blocking function in thread executor"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, func, *args)

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
            4004: "Session not found",
            4005: "Connection timeout"
        }
        return reasons.get(close_code, f"Unknown code {close_code}")

    @database_sync_to_async
    def save_simplified_input(self, team_id, mission_id, student_data, input_data):
        """Save simplified phase input to database"""
        try:
            from .models import SimplifiedPhaseInput, DesignTeam, DesignMission, PhaseCompletionTracker
            
            team = DesignTeam.objects.get(id=team_id)
            mission = DesignMission.objects.get(id=mission_id)
            session = team.session
            
            # Create simplified input record
            phase_input = SimplifiedPhaseInput.objects.create(
                team=team,
                mission=mission,
                session=session,
                student_name=student_data.get('name', 'Anonymous'),
                student_session_id=student_data.get('session_id'),
                input_type=input_data.get('type'),
                input_label=input_data.get('label'),
                selected_value=input_data.get('value'),
                input_order=input_data.get('order', 1),
                time_to_complete_seconds=input_data.get('time_taken', 0)
            )
            
            # Update completion tracking
            tracker, created = PhaseCompletionTracker.objects.get_or_create(
                session=session,
                team=team,
                mission=mission,
                defaults={
                    'total_required_inputs': self._calculate_required_inputs(mission, team),
                    'completed_inputs': 0
                }
            )
            
            tracker.completed_inputs += 1
            tracker.update_completion_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving simplified input: {str(e)}")
            return False

    @database_sync_to_async
    def check_auto_progression(self, team_id, mission_id):
        """Check if team completion triggers auto-progression"""
        try:
            from .models import DesignTeam, DesignMission, PhaseCompletionTracker
            
            team = DesignTeam.objects.get(id=team_id)
            mission = DesignMission.objects.get(id=mission_id)
            session = team.session
            
            # Get completion tracker
            tracker = PhaseCompletionTracker.objects.get(
                session=session,
                team=team,
                mission=mission
            )
            
            result = {
                'should_advance': False,
                'completion_percentage': tracker.completion_percentage,
                'is_ready': tracker.is_ready_to_advance
            }
            
            # Check if this triggers session-wide auto-advancement
            if tracker.is_ready_to_advance and session.design_game.auto_advance_enabled:
                # Check if ALL teams in session are ready (if required)
                if session.design_game.completion_threshold_percentage == 100:
                    all_teams_ready = self._check_all_teams_ready(session, mission)
                    if all_teams_ready:
                        next_mission = self._get_next_mission(session, mission)
                        if next_mission:
                            result.update({
                                'should_advance': True,
                                'current_mission': {
                                    'id': mission.id,
                                    'title': mission.title,
                                    'mission_type': mission.mission_type
                                },
                                'next_mission': {
                                    'id': next_mission.id,
                                    'title': next_mission.title,
                                    'mission_type': next_mission.mission_type
                                },
                                'countdown_seconds': session.design_game.phase_transition_delay
                            })
                else:
                    # Individual team completion is enough
                    next_mission = self._get_next_mission(session, mission)
                    if next_mission:
                        result.update({
                            'should_advance': True,
                            'current_mission': {
                                'id': mission.id,
                                'title': mission.title,
                                'mission_type': mission.mission_type
                            },
                            'next_mission': {
                                'id': next_mission.id,
                                'title': next_mission.title,
                                'mission_type': next_mission.mission_type
                            },
                            'countdown_seconds': session.design_game.phase_transition_delay
                        })
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking auto-progression: {str(e)}")
            return {'should_advance': False, 'completion_percentage': 0, 'is_ready': False}

    @database_sync_to_async  
    def save_teacher_score(self, team_id, mission_id, score, teacher_id):
        """Save teacher score for team's phase completion"""
        try:
            from .models import SimplifiedPhaseInput, DesignTeam, DesignMission
            
            team = DesignTeam.objects.get(id=team_id)
            mission = DesignMission.objects.get(id=mission_id)
            
            # Update scores for all inputs from this team for this mission
            inputs = SimplifiedPhaseInput.objects.filter(
                team=team,
                mission=mission,
                teacher_score__isnull=True
            )
            
            for phase_input in inputs:
                phase_input.teacher_score = score
                phase_input.scored_at = timezone.now()
                phase_input.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving teacher score: {str(e)}")
            return False

    @database_sync_to_async
    def get_mission_data(self, mission_id):
        """Get mission data for broadcasting"""
        try:
            from .models import DesignMission
            
            mission = DesignMission.objects.get(id=mission_id)
            return {
                'id': mission.id,
                'title': mission.title,
                'mission_type': mission.mission_type,
                'description': getattr(mission, 'description', '')
            }
        except Exception as e:
            logger.error(f"Error getting mission data: {str(e)}")
            return {'error': 'Mission data retrieval failed'}

    def _calculate_required_inputs(self, mission, team):
        """Calculate total required inputs for team to complete mission"""
        # This would be based on the mission's input_schema
        # For now, assume each team member needs to complete all inputs
        team_size = len(team.team_members) if team.team_members else 1
        inputs_per_person = len(mission.input_schema.get('inputs', [])) if mission.input_schema else 1
        return team_size * inputs_per_person

    def _check_all_teams_ready(self, session, mission):
        """Check if all teams in session are ready for this mission"""
        from .models import PhaseCompletionTracker
        
        total_teams = session.design_teams.count()
        ready_teams = PhaseCompletionTracker.objects.filter(
            session=session,
            mission=mission,
            is_ready_to_advance=True
        ).count()
        
        return ready_teams >= total_teams

    def _get_next_mission(self, session, current_mission):
        """Get the next mission in sequence"""
        from .models import DesignMission
        
        try:
            next_mission = DesignMission.objects.filter(
                game=session.design_game,
                order=current_mission.order + 1,
                is_active=True
            ).first()
            return next_mission
        except Exception:
            return None

    @database_sync_to_async
    def create_feedback_record(self, team_id, submission_id, message, score, feedback_type, sender_name):
        """Create a new realtime feedback record"""
        try:
            from .models import DesignTeam, SimplifiedPhaseInput, RealtimeFeedback
            
            team = DesignTeam.objects.get(id=team_id)
            session = team.session
            
            submission = None
            if submission_id:
                try:
                    submission = SimplifiedPhaseInput.objects.get(id=submission_id)
                except SimplifiedPhaseInput.DoesNotExist:
                    pass
            
            feedback = RealtimeFeedback.objects.create(
                session=session,
                team=team,
                submission=submission,
                feedback_type=feedback_type,
                sender_type='teacher',
                sender_name=sender_name,
                message=message,
                score=score
            )
            
            return {
                'id': feedback.id,
                'team_id': team_id,
                'message': message,
                'score': score,
                'feedback_type': feedback_type,
                'sender_name': sender_name,
                'created_at': feedback.created_at.isoformat(),
                'submission_id': submission_id
            }
            
        except Exception as e:
            logger.error(f"Error creating feedback record: {str(e)}")
            return None

    async def broadcast_teacher_feedback(self, feedback_data):
        """Broadcast teacher feedback to all session participants"""
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'teacher_feedback_update',
                    'feedback_data': feedback_data,
                    'team_data': {
                        'id': feedback_data['team_id']
                    },
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Mark as sent via WebSocket
            if feedback_data.get('id'):
                await self.mark_feedback_websocket_sent(feedback_data['id'])
                
        except Exception as e:
            logger.error(f"Error broadcasting teacher feedback: {str(e)}")

    @database_sync_to_async
    def mark_feedback_websocket_sent(self, feedback_id):
        """Mark feedback as sent via WebSocket"""
        try:
            from .models import RealtimeFeedback
            feedback = RealtimeFeedback.objects.get(id=feedback_id)
            feedback.mark_websocket_sent()
        except Exception as e:
            logger.error(f"Error marking feedback as sent: {str(e)}")

    async def broadcast_submission_to_teachers(self, result, team_id, mission_id, student_data, input_data):
        """Broadcast student submission to teacher dashboard for real-time review"""
        try:
            # Get team and submission details
            submission_details = await self.get_submission_details(result.get('phase_input_id'))
            
            if submission_details:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'student_submission_for_review',
                        'submission_data': submission_details,
                        'team_data': {
                            'id': team_id,
                            'name': submission_details.get('team_name')
                        },
                        'timestamp': timezone.now().isoformat()
                    }
                )
                
        except Exception as e:
            logger.error(f"Error broadcasting submission to teachers: {str(e)}")

    @database_sync_to_async 
    def get_submission_details(self, phase_input_id):
        """Get detailed submission information for teacher review"""
        try:
            from .models import SimplifiedPhaseInput
            
            submission = SimplifiedPhaseInput.objects.select_related(
                'team', 'mission', 'session'
            ).get(id=phase_input_id)
            
            return {
                'id': submission.id,
                'team_id': submission.team.id,
                'team_name': submission.team.team_name,
                'student_name': submission.student_name,
                'mission_title': submission.mission.title,
                'mission_type': submission.mission.get_mission_type_display(),
                'input_type': submission.get_input_type_display(),
                'input_label': submission.input_label,
                'selected_value': submission.selected_value,
                'submitted_at': submission.submitted_at.isoformat(),
                'teacher_score': submission.teacher_score,
                'needs_review': submission.teacher_score is None
            }
            
        except Exception as e:
            logger.error(f"Error getting submission details: {str(e)}")
            return None

    async def design_ping_monitor(self):
        """Monitor Design Thinking connection health and close if inactive"""
        try:
            while True:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                time_since_ping = timezone.now() - self.last_ping
                if time_since_ping.total_seconds() > self.connection_timeout:
                    logger.warning(f"⏰ Design Thinking connection timeout - Session: {self.session_code}, Connection: {self.connection_id}, Last ping: {time_since_ping.total_seconds()}s ago")
                    await self.close(code=4005)  # Custom timeout code
                    break
                    
        except asyncio.CancelledError:
            logger.info(f"🔄 Design Thinking ping monitor cancelled for connection: {self.connection_id}")
        except Exception as e:
            logger.error(f"💥 Error in Design Thinking ping monitor for connection {self.connection_id}: {str(e)}")