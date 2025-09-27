"""
WebSocket broadcasting utilities for group learning games
"""

import json
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


def broadcast_to_session(session_code, message_type, data, event_type=None):
    """
    Broadcast a message to all WebSocket connections in a session
    
    Args:
        session_code (str): The session code to broadcast to
        message_type (str): Type of message (session_update, phase_changed, etc.)
        data (dict): Data to send with the message
        event_type (str, optional): Specific event type for game_event messages
    """
    if not session_code:
        logger.error("Cannot broadcast: session_code is required")
        return
    
    room_group_name = f'climate_session_{session_code}'
    
    message = {
        'type': message_type.replace('-', '_'),  # Convert to valid method name
    }
    
    # Add data based on message type
    if message_type == 'session_update':
        message['data'] = data
    elif message_type == 'phase_changed':
        message['new_phase'] = data.get('new_phase')
        message['current_round'] = data.get('current_round')
    elif message_type == 'player_joined':
        message['player_name'] = data.get('player_name')
        message['total_players'] = data.get('total_players')
    elif message_type == 'response_received':
        message['responses_count'] = data.get('responses_count')
        message['total_players'] = data.get('total_players')
    elif message_type == 'game_event':
        message['event_type'] = event_type
        message['data'] = data
    elif message_type == 'error_notification':
        message['message'] = data.get('message', 'An error occurred')
    else:
        message['data'] = data
    
    try:
        logger.info(f"🚀 BROADCASTING {message_type} to {room_group_name} - Data: {data}")
        async_to_sync(channel_layer.group_send)(room_group_name, message)
        logger.info(f"✅ Successfully broadcasted {message_type} to session {session_code}")
    except Exception as e:
        logger.error(f"❌ BROADCAST FAILED to session {session_code}: {str(e)}")
        logger.error(f"   Message: {message}")
        logger.error(f"   Room: {room_group_name}")


def broadcast_game_started(session_code):
    """Broadcast that a game has started"""
    broadcast_to_session(
        session_code, 
        'game_event', 
        {'message': 'Game has started!'}, 
        event_type='game_started'
    )


def broadcast_phase_change(session_code, new_phase, current_round):
    """Broadcast phase change to all session participants"""
    logger.info(f"🎯 PHASE CHANGE BROADCAST - Session: {session_code}, Phase: {new_phase}, Round: {current_round}")
    broadcast_to_session(
        session_code,
        'phase_changed',
        {
            'new_phase': new_phase,
            'current_round': current_round
        }
    )


def broadcast_player_joined(session_code, player_name, total_players):
    """Broadcast that a new player joined the session"""
    broadcast_to_session(
        session_code,
        'player_joined',
        {
            'player_name': player_name,
            'total_players': total_players
        }
    )


def broadcast_response_received(session_code, responses_count, total_players):
    """Broadcast that a new response was received"""
    broadcast_to_session(
        session_code,
        'response_received',
        {
            'responses_count': responses_count,
            'total_players': total_players
        }
    )


def broadcast_session_update(session_code, session_data):
    """Broadcast complete session state update"""
    broadcast_to_session(
        session_code,
        'session_update',
        session_data
    )


def broadcast_error(session_code, error_message):
    """Broadcast an error notification to the session"""
    broadcast_to_session(
        session_code,
        'error_notification',
        {'message': error_message}
    )


def broadcast_timer_started(session_code, timer_info):
    """Broadcast timer started event to all participants"""
    broadcast_to_session(
        session_code,
        'timer_started',
        timer_info
    )


def broadcast_timer_update(session_code, timer_info):
    """Broadcast timer update to all participants"""
    broadcast_to_session(
        session_code,
        'timer_update',
        timer_info
    )