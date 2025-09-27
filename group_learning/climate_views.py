from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Q
from django.core.exceptions import ValidationError
import json
import uuid
import random
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

from .models import (
    ClimateGame, ClimateGameSession, ClimateScenario, ClimateQuestion, 
    ClimateOption, ClimatePlayerResponse, ClimateRoundResult
)
from core.models import GameReview
from .websocket_utils import (
    broadcast_game_started, broadcast_phase_change, 
    broadcast_session_update, broadcast_response_received,
    broadcast_player_joined
)


def get_session_status_for_broadcast(session):
    """
    Get session status data for WebSocket broadcasting
    """
    # Count responses for current round
    current_responses = ClimatePlayerResponse.objects.filter(
        climate_session=session,
        round_number=session.current_round
    ).count()
    
    # Use unified count method
    total_players = session.get_active_player_count()
    
    # Get actual student list with roles using unified method
    students_data = []
    for player in session.get_active_players_list():
        students_data.append({
            'player_session_id': player['player_session_id'],
            'role': player['assigned_role'],
            'player_name': player['player_name'] or player['player_session_id']
        })
    
    return {
        'status': session.status,
        'current_phase': session.current_phase,
        'current_round': session.current_round,
        'responses_count': current_responses,
        'total_players': total_players,
        'students': students_data,
        'session_name': f"Climate Session - {session.session_code}",
        'facilitator_name': session.facilitator.username if session.facilitator else "Facilitator",
        'created_at': session.created_at.isoformat() if session.created_at else None,
        'meter_status': session.get_meter_status(),
    }


def climate_game_home(request):
    """
    Climate game landing page with game description and facilitator options
    """
    climate_games = ClimateGame.objects.filter(is_active=True)
    
    context = {
        'climate_games': climate_games,
        'page_title': 'Climate Crisis India - Multiplayer Simulation Game',
        'meta_description': 'Navigate India\'s climate challenges through role-based decision making. A multiplayer simulation for Indian classrooms.',
    }
    return render(request, 'group_learning/climate/game_home.html', context)


def create_climate_session(request):
    """
    Facilitator creates a new climate game session
    """
    if request.method == 'POST':
        game_id = request.POST.get('game_id')
        facilitator_name = request.POST.get('facilitator_name', 'Anonymous')
        
        try:
            climate_game = get_object_or_404(ClimateGame, id=game_id)
            
            # Generate unique session code
            session_code = generate_session_code()
            
            # Create climate game session
            session = ClimateGameSession.objects.create(
                game=climate_game.game_ptr,  # Base Game instance
                climate_game=climate_game,
                session_code=session_code,
                status='waiting',
                current_phase='lobby',
                allow_spectators=False,
                auto_assign_roles=True
            )
            
            # Store facilitator info in session data
            session.session_data = {
                'facilitator_name': facilitator_name,
                'roles_assigned': {},
                'round_timers': {}
            }
            session.save()
            
            messages.success(request, f'Climate game session created! Session code: {session_code}')
            return redirect('group_learning:climate_facilitator_dashboard', session_code=session_code)
            
        except Exception as e:
            messages.error(request, f'Error creating session: {str(e)}')
    
    climate_games = ClimateGame.objects.filter(is_active=True)
    return render(request, 'group_learning/climate/create_session.html', {
        'climate_games': climate_games
    })


def climate_facilitator_dashboard(request, session_code):
    """
    Facilitator dashboard to manage game session
    """
    session = get_object_or_404(ClimateGameSession, session_code=session_code)
    
    # Get current round scenario
    current_scenario = None
    if session.current_round <= 5:
        current_scenario = ClimateScenario.objects.filter(
            game=session.climate_game,
            round_number=session.current_round
        ).first()
    
    # Get player statistics
    responses = ClimatePlayerResponse.objects.filter(climate_session=session)
    total_players = responses.values('player_session_id').distinct().count()
    
    logger.info(f"Dashboard for session {session_code}: Found {responses.count()} total responses, {total_players} unique players")
    
    # Get actual student list with roles for display
    students = []
    unique_players = responses.values('player_session_id', 'assigned_role', 'player_name').distinct()
    
    logger.info(f"Dashboard unique players query result: {list(unique_players)}")
    
    for player in unique_players:
        student_data = {
            'player_session_id': player['player_session_id'],
            'player_name': player['player_name'] or player['player_session_id'],
            'role': player['assigned_role']
        }
        students.append(student_data)
        logger.info(f"Added student to dashboard: {student_data}")
    
    logger.info(f"Final dashboard students list: {students}")
    
    # Role distribution
    role_counts = responses.values('assigned_role').annotate(count=Count('player_session_id', distinct=True))
    
    # Current round progress
    current_round_responses = responses.filter(round_number=session.current_round)
    current_round_completed = current_round_responses.values('player_session_id').distinct().count()
    
    # Get session metadata from session_data
    session_data = session.session_data or {}
    session_name = session_data.get('session_name', f'Climate Session {session_code}')
    facilitator_name = session_data.get('facilitator_name', 'Unknown')
    
    context = {
        'session': session,
        'session_code': session_code,  # Fix: Add missing session_code to context
        'session_name': session_name,
        'facilitator_name': facilitator_name,
        'current_scenario': current_scenario,
        'current_phase': session.current_phase,  # Fix: Add current_phase for JavaScript
        'current_round': session.current_round,  # Fix: Add current_round for template
        'total_players': total_players,
        'students': students,  # Add actual student list for template rendering
        'role_counts': role_counts,
        'current_round_responses': current_round_completed,
        'session_url': request.build_absolute_uri(f'/learn/climate/join/{session_code}/'),
        'meter_status': session.get_meter_status(),
    }
    
    return render(request, 'group_learning/climate/facilitator_dashboard.html', context)


def join_climate_session(request, session_code):
    """
    Players join a climate game session
    """
    session = get_object_or_404(ClimateGameSession, session_code=session_code)
    
    if session.status == 'completed':
        return render(request, 'group_learning/climate/session_ended.html', {'session': session})
    
    # Handle player joining
    if request.method == 'POST':
        # Prevent joining if game is already in progress
        if session.status != 'waiting':
            messages.error(request, 'Cannot join - game has already started')
            return render(request, 'group_learning/climate/join_session.html', {'session': session})
            
        player_name = request.POST.get('player_name', '').strip()
        
        if not player_name:
            messages.error(request, 'Please enter your name')
            return render(request, 'group_learning/climate/join_session.html', {'session': session})
        
        # Generate player session ID
        player_session_id = str(uuid.uuid4())
        
        # Assign role (auto-assign evenly across 5 roles)
        assigned_role = auto_assign_role(session)
        
        # Create placeholder ClimatePlayerResponse to show player in dashboard
        # This allows the facilitator to see who has joined before the game starts
        logger.info(f"Creating ClimatePlayerResponse for player: {player_name} (ID: {player_session_id}) in session {session_code} with role {assigned_role}")
        
        try:
            response_entry = ClimatePlayerResponse.objects.create(
                climate_session=session,
                player_name=player_name,
                player_session_id=player_session_id,
                assigned_role=assigned_role,
                round_number=0,  # Special round number for lobby entries
                climate_scenario=None,  # No scenario yet
                selected_option=None,  # No response yet
                response_time=0
            )
            logger.info(f"Successfully created ClimatePlayerResponse ID: {response_entry.id}")
        except Exception as e:
            logger.error(f"Failed to create ClimatePlayerResponse: {str(e)}")
            logger.error(f"Full traceback: ", exc_info=True)
            messages.error(request, 'Error joining session. Please try again.')
            return render(request, 'group_learning/climate/join_session.html', {'session': session})
        
        # Store player info in session
        request.session['climate_player_session_id'] = player_session_id
        request.session['climate_player_name'] = player_name
        request.session['climate_assigned_role'] = assigned_role
        request.session['climate_session_code'] = session_code
        request.session.save()  # Explicitly save session data
        
        # Broadcast player joined via WebSocket using unified count method
        total_players = session.get_active_player_count()
        logger.info(f"Broadcasting player joined: {player_name} to session {session_code}, total players now: {total_players}")
        broadcast_player_joined(session_code, player_name, total_players)
        
        # Also broadcast full session update to refresh student lists
        session_data = get_session_status_for_broadcast(session)
        broadcast_session_update(session_code, session_data)
        
        return redirect('group_learning:climate_game_lobby', session_code=session_code)
    
    return render(request, 'group_learning/climate/join_session.html', {'session': session})


def climate_game_lobby(request, session_code):
    """
    Game lobby where players wait for game to start
    """
    session = get_object_or_404(ClimateGameSession, session_code=session_code)
    
    # Check if player is properly registered
    player_session_id = request.session.get('climate_player_session_id')
    player_name = request.session.get('climate_player_name')
    assigned_role = request.session.get('climate_assigned_role')
    
    if not all([player_session_id, player_name, assigned_role]):
        return redirect('group_learning:join_climate_session', session_code=session_code)
    
    # If game has started, redirect to current phase
    if session.status == 'in_progress':
        logger.info(f"Player {player_name} accessing lobby but game already started. Redirecting to game play. Session status: {session.status}, phase: {session.current_phase}")
        return redirect('group_learning:climate_game_play', session_code=session_code)
    
    # Add additional check for any non-lobby phase
    if session.current_phase != 'lobby':
        logger.info(f"Player {player_name} accessing lobby but game in phase {session.current_phase}. Redirecting to game play.")
        return redirect('group_learning:climate_game_play', session_code=session_code)
    
    # Get other players in lobby
    players_in_lobby = ClimatePlayerResponse.objects.filter(
        climate_session=session
    ).values('player_name', 'assigned_role').distinct()
    
    context = {
        'session': session,
        'player_name': player_name,
        'assigned_role': assigned_role,
        'role_display': dict(ClimateQuestion.ROLE_CHOICES)[assigned_role],
        'players_in_lobby': players_in_lobby,
        'meter_status': session.get_meter_status(),
    }
    
    return render(request, 'group_learning/climate/game_lobby.html', context)


def climate_game_play(request, session_code):
    """
    Main game play interface - routes to appropriate phase
    """
    session = get_object_or_404(ClimateGameSession, session_code=session_code)
    
    # Check player registration
    player_session_id = request.session.get('climate_player_session_id')
    if not player_session_id:
        return redirect('group_learning:join_climate_session', session_code=session_code)
    
    # Route based on current game phase
    if session.current_phase == 'lobby':
        return redirect('group_learning:climate_game_lobby', session_code=session_code)
    elif session.current_phase == 'scenario_intro':
        return climate_scenario_intro(request, session)
    elif session.current_phase == 'question_phase':
        return climate_question_phase(request, session)
    elif session.current_phase == 'results_feedback':
        return climate_results_feedback(request, session)
    elif session.current_phase == 'game_complete':
        return climate_game_complete(request, session)
    else:
        return climate_game_lobby(request, session_code)


def climate_scenario_intro(request, session):
    """
    Display scenario introduction with context and timing
    """
    current_scenario = ClimateScenario.objects.get(
        game=session.climate_game,
        round_number=session.current_round
    )
    
    player_name = request.session.get('climate_player_name')
    assigned_role = request.session.get('climate_assigned_role')
    
    context = {
        'session': session,
        'scenario': current_scenario,
        'player_name': player_name,
        'assigned_role': assigned_role,
        'role_display': dict(ClimateQuestion.ROLE_CHOICES)[assigned_role],
        'meter_status': session.get_meter_status(),
        'round_progress': f"{session.current_round}/5",
    }
    
    return render(request, 'group_learning/climate/scenario_intro.html', context)


def climate_question_phase(request, session):
    """
    Players answer their role-specific questions
    """
    player_session_id = request.session.get('climate_player_session_id')
    player_name = request.session.get('climate_player_name')
    assigned_role = request.session.get('climate_assigned_role')
    
    # Get current scenario and question for player's role with error handling
    try:
        current_scenario = ClimateScenario.objects.get(
            game=session.climate_game,
            round_number=session.current_round
        )
    except ClimateScenario.DoesNotExist:
        logger.error(f"No scenario found for game {session.climate_game} round {session.current_round}")
        messages.error(request, f'Game scenario not found for round {session.current_round}. Please contact the facilitator.')
        return redirect('group_learning:climate_game_lobby', session_code=session.session_code)
    
    try:
        question = ClimateQuestion.objects.get(
            scenario=current_scenario,
            role=assigned_role
        )
    except ClimateQuestion.DoesNotExist:
        logger.error(f"No question found for scenario {current_scenario} role {assigned_role}")
        messages.error(request, f'Question not found for your role ({assigned_role}). Please contact the facilitator.')
        return redirect('group_learning:climate_game_lobby', session_code=session.session_code)
    
    # Check if player already answered
    existing_response = ClimatePlayerResponse.objects.filter(
        climate_session=session,
        player_session_id=player_session_id,
        climate_scenario=current_scenario
    ).first()
    
    if existing_response:
        # Player already answered, show waiting screen
        return render(request, 'group_learning/climate/waiting_for_others.html', {
            'session': session,
            'scenario': current_scenario,
            'selected_option': existing_response.selected_option,
            'meter_status': session.get_meter_status(),
        })
    
    # Handle form submission
    if request.method == 'POST':
        option_id = request.POST.get('selected_option')
        response_time = float(request.POST.get('response_time', 60))
        
        try:
            selected_option = ClimateOption.objects.get(id=option_id, question=question)
            
            # Create player response
            response = ClimatePlayerResponse.objects.create(
                climate_session=session,
                climate_scenario=current_scenario,
                selected_option=selected_option,
                player_name=player_name,
                player_session_id=player_session_id,
                assigned_role=assigned_role,
                response_time=response_time,
                round_number=session.current_round
            )
            
            # Broadcast response received via WebSocket
            try:
                # Calculate current responses for this round
                responses_count = ClimatePlayerResponse.objects.filter(
                    climate_session=session,
                    climate_scenario=current_scenario
                ).count()
                
                broadcast_response_received(
                    session.session_code,
                    responses_count,
                    session.get_active_player_count()
                )
            except Exception as ws_error:
                logger.warning(f"WebSocket broadcast failed for session {session.session_code}: {str(ws_error)}")
                # Continue with game flow even if WebSocket fails
            
            # Return JSON response for AJAX
            return JsonResponse({
                'success': True,
                'message': 'Response submitted successfully',
                'selected_option': selected_option.option_letter,
                'redirect_url': f'/learn/climate/{session.session_code}/play/'
            })
            
        except ClimateOption.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid option selected'
            })
        except Exception as e:
            logger.error(f"Error saving player response: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while submitting your response'
            })
    
    context = {
        'session': session,
        'scenario': current_scenario,
        'question': question,
        'options': question.options.all(),
        'player_name': player_name,
        'assigned_role': assigned_role,
        'role_display': dict(ClimateQuestion.ROLE_CHOICES)[assigned_role],
        'meter_status': session.get_meter_status(),
        'round_progress': f"{session.current_round}/5",
    }
    
    return render(request, 'group_learning/climate/question_phase.html', context)


def climate_impact_results(request, session_code):
    """
    Show detailed impact results and reasoning for student's decision
    """
    session = get_object_or_404(ClimateGameSession, session_code=session_code)
    
    # Check player registration
    player_session_id = request.session.get('climate_player_session_id')
    player_name = request.session.get('climate_player_name')
    assigned_role = request.session.get('climate_assigned_role')
    
    if not all([player_session_id, player_name, assigned_role]):
        return redirect('group_learning:join_climate_session', session_code=session_code)
    
    # Get current scenario and player's response
    current_scenario = ClimateScenario.objects.get(
        game=session.climate_game,
        round_number=session.current_round
    )
    
    # Get player's response
    player_response = ClimatePlayerResponse.objects.filter(
        climate_session=session,
        player_session_id=player_session_id,
        climate_scenario=current_scenario
    ).first()
    
    if not player_response:
        return redirect('group_learning:climate_game_play', session_code=session_code)
    
    # Get all options for this question to show what would have happened
    question = ClimateQuestion.objects.get(
        scenario=current_scenario,
        role=assigned_role
    )
    all_options = question.options.all()
    
    # Generate detailed reasoning for each option
    impact_analysis = []
    for option in all_options:
        reasoning = generate_detailed_impact_reasoning(
            option, 
            assigned_role, 
            current_scenario,
            is_selected=(option.id == player_response.selected_option.id)
        )
        impact_analysis.append({
            'option': option,
            'reasoning': reasoning,
            'is_selected': option.id == player_response.selected_option.id
        })
    
    context = {
        'session': session,
        'scenario': current_scenario,
        'player_response': player_response,
        'player_name': player_name,
        'assigned_role': assigned_role,
        'role_display': dict(ClimateQuestion.ROLE_CHOICES)[assigned_role],
        'impact_analysis': impact_analysis,
        'meter_status': session.get_meter_status(),
        'round_progress': f"{session.current_round}/5",
    }
    
    return render(request, 'group_learning/climate/impact_results.html', context)


def climate_results_feedback(request, session):
    """
    Show round results and meter changes
    """
    current_scenario = ClimateScenario.objects.get(
        game=session.climate_game,
        round_number=session.current_round
    )
    
    # Get or create round results
    round_result, created = ClimateRoundResult.objects.get_or_create(
        session=session,
        scenario=current_scenario,
        defaults={
            'response_summary': {},
            'meter_changes': {},
            'meters_after': session.get_meter_status(),
            'outcome_narrative': '',
            'learning_outcome': ''
        }
    )
    
    if created:
        # Calculate results for this round
        calculate_round_results(session, current_scenario, round_result)
    
    context = {
        'session': session,
        'scenario': current_scenario,
        'round_result': round_result,
        'meter_status': session.get_meter_status(),
        'round_progress': f"{session.current_round}/5",
    }
    
    return render(request, 'group_learning/climate/results_feedback.html', context)


def climate_game_complete(request, session):
    """
    Game completion screen with final results and review
    """
    # Get all round results
    round_results = ClimateRoundResult.objects.filter(session=session).order_by('scenario__round_number')
    
    # Final meter status
    final_meters = session.get_meter_status()
    
    # Calculate overall performance
    total_climate_score = sum([
        final_meters['climate_resilience'],
        final_meters['environmental_health'],
        100 - abs(50 - final_meters['gdp']),  # Balanced economy is good
        final_meters['public_morale']
    ]) / 4
    
    context = {
        'session': session,
        'round_results': round_results,
        'final_meters': final_meters,
        'total_climate_score': round(total_climate_score),
        'game_review_enabled': True,  # Enable GameReview integration
    }
    
    return render(request, 'group_learning/climate/game_complete.html', context)


# AJAX API endpoints for real-time updates

@csrf_exempt
@require_http_methods(["POST"])
def start_climate_game(request, session_code):
    """
    Facilitator starts the climate game with atomic state transitions
    """
    from django.db import transaction
    
    session = get_object_or_404(ClimateGameSession, session_code=session_code)
    
    if session.status == 'waiting':
        # Atomic transaction ensures database consistency
        with transaction.atomic():
            old_phase = session.current_phase
            session.status = 'in_progress'
            session.start_new_round(1)
            session.save()
            
            # Log state transition for production monitoring
            logger.info(
                f"[STATE_TRANSITION] Session {session_code}: {old_phase} -> {session.current_phase}",
                extra={
                    'session_code': session_code,
                    'old_phase': old_phase,
                    'new_phase': session.current_phase,
                    'round': session.current_round,
                    'status': session.status
                }
            )
        
        # After successful database commit, broadcast WebSocket events
        try:
            # Broadcast game started event via WebSocket
            broadcast_game_started(session_code)
            
            # Broadcast phase change
            broadcast_phase_change(
                session_code, 
                session.current_phase, 
                session.current_round
            )
            
            logger.info(f"[WEBSOCKET] Successfully broadcasted phase change for session {session_code}")
            
        except Exception as broadcast_error:
            logger.error(
                f"[WEBSOCKET_ERROR] Failed to broadcast phase change for session {session_code}: {broadcast_error}",
                exc_info=True
            )
            # Don't fail the entire operation if WebSocket broadcast fails
            # The polling fallback will handle client updates
        
        return JsonResponse({
            'success': True,
            'message': 'Climate game started!',
            'current_phase': session.current_phase
        })
    
    return JsonResponse({'success': False, 'message': 'Game already started'})


@csrf_exempt 
@require_http_methods(["POST"])
def advance_climate_phase(request, session_code):
    """
    Facilitator advances to next phase
    """
    session = get_object_or_404(ClimateGameSession, session_code=session_code)
    new_phase = request.POST.get('phase')
    
    # If no phase specified, determine next phase automatically
    if not new_phase:
        if session.current_phase == 'scenario_intro':
            new_phase = 'question_phase'
        elif session.current_phase == 'question_phase':
            new_phase = 'results_feedback'
        elif session.current_phase == 'results_feedback':
            if session.current_round < 5:
                new_phase = 'scenario_intro'
            else:
                new_phase = 'game_complete'
        else:
            new_phase = 'question_phase'  # Default fallback
    
    valid_phases = ['scenario_intro', 'question_phase', 'results_feedback', 'round_complete', 'game_complete']
    
    if new_phase in valid_phases:
        session.advance_phase(new_phase)
        
        # If starting new round
        if new_phase == 'scenario_intro' and session.current_round < 5:
            session.start_new_round(session.current_round + 1)
        
        # Auto-start timer when entering question phase
        if new_phase == 'question_phase' and session.question_timer_enabled:
            session.start_timer()  # Uses default 10min duration
            
            # Broadcast timer started
            from .websocket_utils import broadcast_timer_started
            timer_info = session.get_timer_info()
            broadcast_timer_started(session_code, timer_info)
        
        # Broadcast phase change via WebSocket
        broadcast_phase_change(
            session_code,
            session.current_phase,
            session.current_round
        )
        
        return JsonResponse({
            'success': True,
            'current_phase': session.current_phase,
            'current_round': session.current_round
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid phase'})


def get_climate_session_status(request, session_code):
    """
    Get real-time session status for polling
    """
    session = get_object_or_404(ClimateGameSession, session_code=session_code)
    
    # Count responses for current round
    current_responses = ClimatePlayerResponse.objects.filter(
        climate_session=session,
        round_number=session.current_round
    ).count()
    
    total_players = ClimatePlayerResponse.objects.filter(
        climate_session=session
    ).values('player_session_id').distinct().count()
    
    return JsonResponse({
        'status': session.status,
        'current_phase': session.current_phase,
        'current_round': session.current_round,
        'responses_count': current_responses,
        'total_players': total_players,
        'meter_status': session.get_meter_status(),
        'phase_start_time': session.phase_start_time.isoformat() if session.phase_start_time else None
    })


# Helper functions

def generate_session_code():
    """Generate a unique 6-character session code"""
    import string
    import random
    
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not ClimateGameSession.objects.filter(session_code=code).exists():
            return code


def auto_assign_role(session):
    """Auto-assign roles evenly across players"""
    roles = ['government', 'business', 'farmer', 'urban_citizen', 'ngo_worker']
    
    # Count existing role assignments
    role_counts = defaultdict(int)
    existing_responses = ClimatePlayerResponse.objects.filter(climate_session=session)
    
    for response in existing_responses:
        role_counts[response.assigned_role] += 1
    
    # Assign role with least players
    min_count = min(role_counts.values()) if role_counts else 0
    available_roles = [role for role in roles if role_counts[role] <= min_count]
    
    return random.choice(available_roles)


def calculate_round_results(session, scenario, round_result):
    """Calculate aggregated results and meter changes for a round"""
    responses = ClimatePlayerResponse.objects.filter(
        climate_session=session,
        climate_scenario=scenario
    )
    
    # Aggregate response summary by role
    response_summary = {}
    total_meter_changes = {'climate_resilience': 0, 'gdp': 0, 'public_morale': 0, 'environmental_health': 0}
    
    for role, _ in ClimateQuestion.ROLE_CHOICES:
        role_responses = responses.filter(assigned_role=role)
        role_total = role_responses.count()
        
        if role_total > 0:
            role_summary = {}
            for option in ['a', 'b', 'c', 'd']:
                option_count = role_responses.filter(selected_option__option_letter=option).count()
                percentage = round((option_count / role_total) * 100)
                role_summary[option] = {
                    'count': option_count,
                    'percentage': percentage
                }
            
            response_summary[role] = role_summary
            
            # Calculate weighted meter changes for this role
            for response in role_responses:
                option_outcome = response.selected_option.outcome_logic
                for meter, change in option_outcome.items():
                    total_meter_changes[meter] += change / role_total
    
    # Apply meter changes to session
    session.update_meters(total_meter_changes)
    
    # Generate narrative based on choices
    outcome_narrative = generate_outcome_narrative(scenario, response_summary, total_meter_changes)
    learning_outcome = generate_learning_outcome(scenario, response_summary)
    
    # Update round result
    round_result.response_summary = response_summary
    round_result.meter_changes = total_meter_changes
    round_result.meters_after = session.get_meter_status()
    round_result.outcome_narrative = outcome_narrative
    round_result.learning_outcome = learning_outcome
    round_result.save()


def generate_outcome_narrative(scenario, response_summary, meter_changes):
    """Generate narrative text based on player choices"""
    narratives = {
        1: {  # Delhi Air Pollution
            'positive': "Coordinated action across government, business, and citizens shows promise. Air quality improvements visible as enforcement combines with voluntary measures.",
            'mixed': "Half-measures and conflicting priorities create modest progress. Some sectors act while others resist, leading to uneven results.",
            'negative': "Lack of coordination and blame games worsen the crisis. Economic interests clash with environmental needs as pollution persists."
        },
        2: {  # Mumbai Floods  
            'positive': "Swift emergency response and sustainable infrastructure investment minimize flood damage. Community resilience builds for future challenges.",
            'mixed': "Emergency funds provide immediate relief but long-term planning suffers. Recovery is partial and vulnerability remains high.",
            'negative': "Short-sighted responses and resource misallocation lead to prolonged suffering. Infrastructure gaps widen as blame games continue."
        },
        # Add narratives for rounds 3, 4, 5...
    }
    
    # Determine overall outcome based on meter changes
    avg_change = sum(meter_changes.values()) / len(meter_changes)
    
    if avg_change > 5:
        outcome_type = 'positive'
    elif avg_change > -5:
        outcome_type = 'mixed'
    else:
        outcome_type = 'negative'
    
    return narratives.get(scenario.round_number, {}).get(outcome_type, 
        "The complex interplay of decisions creates mixed outcomes with both progress and setbacks.")


def generate_detailed_impact_reasoning(option, role, scenario, is_selected=False):
    """
    Generate detailed cause-and-effect reasoning for each climate option
    """
    # Base reasoning templates for different roles and scenarios
    reasoning_templates = {
        'government': {
            1: {  # Delhi Air Pollution
                'a': {
                    'environmental': "Immediate pollution controls reduce PM2.5 but may face industry resistance",
                    'economic': "Short-term costs offset by long-term health savings and improved productivity",
                    'social': "Public health improves rapidly, building trust in government action"
                },
                'b': {
                    'environmental': "Gradual approach allows adaptation but pollution persists longer",
                    'economic': "Balanced impact spreads costs over time, less industry disruption",
                    'social': "Mixed public response - some appreciate caution, others want faster action"
                },
                'c': {
                    'environmental': "Technology focus addresses root causes but takes time to show results",
                    'economic': "High initial investment in green tech, but creates new economic opportunities",
                    'social': "Innovation approach popular with educated urban population"
                },
                'd': {
                    'environmental': "Limited action maintains status quo, pollution crisis continues",
                    'economic': "No immediate economic disruption but health costs mount",
                    'social': "Public frustration increases, loss of confidence in governance"
                }
            },
            2: {  # Mumbai Floods
                'a': {
                    'environmental': "Emergency response saves lives but doesn't address flood infrastructure gaps",
                    'economic': "High rescue costs but prevents economic disruption from prolonged flooding",
                    'social': "Swift action builds public trust in emergency management capabilities"
                },
                'b': {
                    'environmental': "Balanced approach protects both people and infrastructure systems",
                    'economic': "Resource allocation spreads costs across immediate and long-term needs",
                    'social': "Coordinated response demonstrates government planning and competence"
                },
                'c': {
                    'environmental': "Infrastructure investment reduces future flood risk and environmental damage",
                    'economic': "Large upfront investment in drainage and flood barriers",
                    'social': "Long-term thinking appreciated but some may criticize slow emergency response"
                },
                'd': {
                    'environmental': "Minimal response allows flooding to persist, causing environmental damage",
                    'economic': "Lower immediate costs but massive economic losses from flood damage",
                    'social': "Public outrage over inadequate emergency response and preparedness"
                }
            },
            3: {  # Chennai Water Shortage
                'a': {
                    'environmental': "Industrial water cuts reduce pollution but stress on water table continues",
                    'economic': "Production slowdowns hurt economy but prevent unsustainable resource depletion",
                    'social': "Tough decisions build long-term trust despite short-term anger from affected sectors"
                },
                'b': {
                    'environmental': "Private tankers exploit groundwater reserves, accelerating aquifer depletion",
                    'economic': "Quick fix maintains business continuity but creates expensive water dependency",
                    'social': "Inequality grows as only wealthy access clean water through private markets"
                },
                'c': {
                    'environmental': "Rainwater harvesting reduces groundwater dependency and recharges aquifers",
                    'economic': "High upfront infrastructure costs but long-term water security for Chennai",
                    'social': "Community participation in harvesting builds collective climate resilience"
                },
                'd': {
                    'environmental': "Inter-state blame games delay action while water crisis deepens",
                    'economic': "Administrative costs rise while core water problems remain unsolved",
                    'social': "Political tensions worsen as Tamil Nadu conflicts with neighboring states"
                }
            },
            4: {  # Migration & Heatwave
                'a': {
                    'environmental': "Job schemes in green sectors help climate adaptation while providing livelihoods",
                    'economic': "Massive public investment strains budget but builds economic resilience",
                    'social': "Government intervention builds trust and prevents social unrest from displacement"
                },
                'b': {
                    'environmental': "Settlement demolition creates homelessness but prevents unsanitary urban sprawl",
                    'economic': "Short-term savings on services but potential legal costs and compensation",
                    'social': "Harsh measures trigger humanitarian outcry and damage government credibility"
                },
                'c': {
                    'environmental': "Business incentives may accelerate industrial pollution if not regulated properly",
                    'economic': "Tax breaks reduce revenue but may stimulate job creation and economic growth",
                    'social': "Private sector involvement creates jobs but risks worker exploitation"
                },
                'd': {
                    'environmental': "Border restrictions trap climate migrants in increasingly uninhabitable areas",
                    'economic': "Lower urban service costs but economic losses from reduced labor mobility",
                    'social': "Enforcement creates humanitarian crisis and inter-state political tensions"
                }
            },
            5: {  # National Election/Policy
                'a': {
                    'environmental': "Ambitious climate commitments drive renewable energy and forest conservation",
                    'economic': "Green transition costs but positions India as clean technology leader",
                    'social': "Climate action builds youth support but faces resistance from traditional industries"
                },
                'b': {
                    'environmental': "Economic focus delays climate action and accelerates environmental degradation",
                    'economic': "Short-term growth prioritized but long-term climate costs mounting",
                    'social': "Employment promises popular but environmental groups and youth feel betrayed"
                },
                'c': {
                    'environmental': "Multi-stakeholder panels ensure balanced environmental and economic policies",
                    'economic': "Inclusive process slower but creates buy-in for sustainable development",
                    'social': "Democratic participation builds trust but may create gridlock in decision-making"
                },
                'd': {
                    'environmental': "Political blame games prevent coordinated climate action across states",
                    'economic': "Policy uncertainty discourages investment in clean energy and adaptation",
                    'social': "Divisive politics fragments climate movement and delays urgent action"
                }
            }
        },
        'business': {
            1: {  # Delhi Air Pollution  
                'a': {
                    'environmental': "Industry compliance reduces emissions but requires significant operational changes",
                    'economic': "Higher compliance costs but access to green markets and financing",
                    'social': "Demonstrates corporate responsibility, improves brand reputation"
                },
                'b': {
                    'environmental': "Moderate changes reduce some emissions while maintaining production",
                    'economic': "Balanced approach minimizes disruption while showing progress",
                    'social': "Stakeholder approval for pragmatic approach to environmental challenges"
                },
                'c': {
                    'environmental': "Innovation focus creates breakthrough solutions for industry-wide adoption",
                    'economic': "R&D investment pays off through competitive advantage and new markets",
                    'social': "Leadership position in green technology enhances corporate image"
                },
                'd': {
                    'environmental': "Minimal action perpetuates pollution, potential regulatory backlash",
                    'economic': "Short-term cost savings but risk of penalties and market exclusion",
                    'social': "Public criticism and potential consumer boycotts affect reputation"
                }
            },
            2: {  # Mumbai Floods
                'a': {
                    'environmental': "Business resources support emergency relief and community recovery",
                    'economic': "Immediate costs for employee safety and business continuity planning",
                    'social': "Corporate social responsibility enhances community relations and brand image"
                },
                'b': {
                    'environmental': "Balanced approach maintains operations while supporting flood response",
                    'economic': "Moderate costs while protecting business assets and employee welfare",
                    'social': "Stakeholder approval for pragmatic response to emergency situation"
                },
                'c': {
                    'environmental': "Long-term flood resilience investment protects business and community",
                    'economic': "Significant infrastructure investment but improved future flood protection",
                    'social': "Leadership in climate adaptation demonstrates forward-thinking management"
                },
                'd': {
                    'environmental': "Limited flood response may worsen community environmental damage",
                    'economic': "Short-term cost savings but risk of flood damage and reputation loss",
                    'social': "Community criticism for inadequate support during emergency"
                }
            },
            3: {  # Chennai Water Shortage
                'a': {
                    'environmental': "Water recycling and conservation reduce industrial environmental footprint",
                    'economic': "Initial investment in water tech but operational cost savings long-term",
                    'social': "Industry leadership in sustainability builds brand reputation and employee pride"
                },
                'b': {
                    'environmental': "Tanker water depletes regional groundwater and increases transportation emissions",
                    'economic': "Higher water costs but maintains full production capacity and profits",
                    'social': "Public anger over 'water mafia' tactics and perceived corporate greed"
                },
                'c': {
                    'environmental': "NGO partnerships create community-scale water conservation impact",
                    'economic': "Shared costs reduce individual burden while building stakeholder goodwill",
                    'social': "Cross-sector collaboration demonstrates corporate social responsibility"
                },
                'd': {
                    'environmental': "Priority water access strains already depleted Chennai aquifers",
                    'economic': "Government support maintains operations but creates dependency on subsidies",
                    'social': "Corporate privilege during crisis triggers protests and boycott threats"
                }
            },
            4: {  # Migration & Heatwave
                'a': {
                    'environmental': "Skills training programs may include green technology and climate adaptation",
                    'economic': "Higher training costs but access to skilled workforce and government incentives",
                    'social': "Inclusive hiring builds positive reputation and demonstrates corporate responsibility"
                },
                'b': {
                    'environmental': "Labor exploitation contributes to urban environmental degradation and slums",
                    'economic': "Lower labor costs boost short-term profits but creates long-term instability",
                    'social': "Worker exploitation triggers activism, unions, and potential legal action"
                },
                'c': {
                    'environmental': "Government partnerships may include environmental compliance requirements",
                    'economic': "Wage support reduces labor costs while maintaining operations during crisis",
                    'social': "Public-private cooperation demonstrates shared responsibility for migration crisis"
                },
                'd': {
                    'environmental': "Automation reduces human environmental impact but increases e-waste and energy use",
                    'economic': "Job automation saves costs but reduces demand for workers and local consumption",
                    'social': "Technology displacement worsens unemployment and social tensions during migration crisis"
                }
            },
            5: {  # National Election/Policy
                'a': {
                    'environmental': "Green technology investment reduces emissions and creates sustainable business models",
                    'economic': "Clean tech leadership positions business for future markets and international opportunities",
                    'social': "Environmental leadership builds brand reputation and attracts conscious consumers"
                },
                'b': {
                    'environmental': "Anti-climate lobbying delays environmental regulations and perpetuates pollution",
                    'economic': "Short-term regulatory relief but long-term market risks from climate impacts",
                    'social': "Corporate resistance to climate action faces growing public criticism and boycotts"
                },
                'c': {
                    'environmental': "Multi-sector climate council balances business needs with environmental protection",
                    'economic': "Collaborative approach reduces regulatory uncertainty and promotes innovation",
                    'social': "Cross-sector leadership demonstrates shared responsibility for climate solutions"
                },
                'd': {
                    'environmental': "Business inaction on climate allows environmental degradation to continue",
                    'economic': "No additional costs but increasing vulnerability to climate risks and regulations",
                    'social': "Corporate apathy disappoints stakeholders and damages long-term business relationships"
                }
            }
        },
        'farmer': {
            1: {  # Delhi Air Pollution
                'a': {
                    'environmental': "Stubble burning alternatives reduce air pollution but require new practices",
                    'economic': "Government support for alternatives offsets transition costs",
                    'social': "Community cooperation needed for widespread adoption of new methods"
                },
                'b': {
                    'environmental': "Gradual transition reduces some burning while farmers adapt slowly",
                    'economic': "Mixed financial impact as some areas get support, others wait",
                    'social': "Rural-urban divide as farmers feel pressure from city dwellers"
                },
                'c': {
                    'environmental': "Technology solutions provide efficient alternatives to crop burning",
                    'economic': "Mechanization costs high initially but improve long-term productivity",
                    'social': "Tech adoption varies by farmer education and resource levels"
                },
                'd': {
                    'environmental': "Continued burning maintains pollution levels, especially in winter",
                    'economic': "No change in farming costs but risk of future penalties",
                    'social': "Blame from urban areas creates tension between communities"
                }
            },
            2: {  # Mumbai Floods
                'a': {
                    'environmental': "Immediate crop protection reduces flood damage to agricultural land",
                    'economic': "Emergency costs for protecting livestock and crops from flood damage",
                    'social': "Rural community cooperation in flood response and recovery efforts"
                },
                'b': {
                    'environmental': "Balanced protection of crops and support for urban flood relief",
                    'economic': "Moderate costs while maintaining agricultural productivity during floods",
                    'social': "Rural-urban solidarity in emergency response demonstrates unity"
                },
                'c': {
                    'environmental': "Sustainable farming practices reduce flood impact and soil erosion",
                    'economic': "Investment in flood-resistant crops and drainage improves long-term yields",
                    'social': "Innovation in climate-smart agriculture attracts support and recognition"
                },
                'd': {
                    'environmental': "No flood adaptation increases agricultural vulnerability to climate change",
                    'economic': "Short-term savings but risk of major crop losses from flooding",
                    'social': "Rural communities isolated during emergencies, lacking urban support"
                }
            },
            3: {  # Chennai Water Shortage
                'a': {
                    'environmental': "Drought-resistant crops reduce water stress and maintain soil health",
                    'economic': "Crop transition costs but protection against future drought losses",
                    'social': "Innovation attracts government support and inspires neighboring farmers"
                },
                'b': {
                    'environmental': "Demanding water priority worsens urban-rural tensions over resources",
                    'economic': "Maintained irrigation but political costs and potential backlash",
                    'social': "Food producers assert rights but risk being seen as selfish during crisis"
                },
                'c': {
                    'environmental': "Illegal borewells accelerate groundwater depletion and land subsidence",
                    'economic': "Immediate water access but risk of penalties and borewell failure",
                    'social': "Desperate survival measures create conflicts with environmental regulations"
                },
                'd': {
                    'environmental': "Cooperative infrastructure reduces water waste and improves efficiency",
                    'economic': "Shared costs make water conservation affordable for small farmers",
                    'social': "Rural collaboration strengthens farming community bonds and bargaining power"
                }
            },
            4: {  # Migration & Heatwave
                'a': {
                    'environmental': "Land cooperation enables climate-smart agriculture and soil conservation",
                    'economic': "Shared resources reduce individual costs and improve collective bargaining power",
                    'social': "Community farming builds solidarity but requires overcoming traditional land disputes"
                },
                'b': {
                    'environmental': "Corporate leasing may introduce intensive farming that degrades soil health",
                    'economic': "Guaranteed lease income provides security but loss of land control",
                    'social': "Corporate farming displaces traditional rural culture and community relationships"
                },
                'c': {
                    'environmental': "Livestock adaptation reduces crop vulnerability but increases methane emissions",
                    'economic': "Diversified income from animals but requires new skills and veterinary costs",
                    'social': "Traditional farming shift creates community learning opportunities"
                },
                'd': {
                    'environmental': "Rural-urban migration abandons agricultural land and reduces local food production",
                    'economic': "Urban income opportunities but loss of family land and agricultural heritage",
                    'social': "Migration fragments rural communities and creates urban adjustment challenges"
                }
            },
            5: {  # National Election/Policy
                'a': {
                    'environmental': "Climate-smart agriculture lobby promotes sustainable farming and biodiversity",
                    'economic': "Green farming subsidies support transition but require collective action",
                    'social': "Farmer unity on climate builds political influence and cross-regional solidarity"
                },
                'b': {
                    'environmental': "Cash demands without sustainability may accelerate environmental degradation",
                    'economic': "Immediate compensation provides relief but unsustainable long-term burden",
                    'social': "Economic focus popular but may conflict with environmental constituencies"
                },
                'c': {
                    'environmental': "Supporting eco-friendly parties aligns farming with environmental protection",
                    'economic': "Green party policies may prioritize environment over agricultural subsidies",
                    'social': "Environmental politics builds alliances but risks traditional farming vote splits"
                },
                'd': {
                    'environmental': "Food supply strikes disrupt climate policy discussions and urban-rural cooperation",
                    'economic': "Supply disruption creates short-term leverage but damages farmer-consumer relationships",
                    'social': "Aggressive tactics may backfire and reduce public sympathy for farming challenges"
                }
            }
        },
        'urban_citizen': {
            1: {  # Delhi Air Pollution
                'a': {
                    'environmental': "Active participation in pollution reduction creates immediate local improvements",
                    'economic': "Personal costs for green alternatives but health savings long-term",
                    'social': "Community mobilization builds collective action for clean air"
                },
                'b': {
                    'environmental': "Moderate lifestyle changes contribute to gradual air quality improvement",
                    'economic': "Balanced approach to green living without major financial strain",
                    'social': "Social pressure to participate while maintaining personal convenience"
                },
                'c': {
                    'environmental': "Supporting clean technology accelerates adoption of pollution solutions",
                    'economic': "Higher upfront costs for green tech but operational savings",
                    'social': "Early adopter status influences community adoption of clean technologies"
                },
                'd': {
                    'environmental': "Minimal lifestyle change means continued exposure to polluted air",
                    'economic': "No change in spending but increasing health costs over time",
                    'social': "Free-rider problem as others bear cost of pollution reduction"
                }
            },
            2: {  # Mumbai Floods
                'a': {
                    'environmental': "Community volunteering supports flood relief and environmental cleanup",
                    'economic': "Personal costs for flood preparation and emergency supplies",
                    'social': "Active citizenship builds community resilience and social cohesion"
                },
                'b': {
                    'environmental': "Moderate flood preparation balances personal and community needs",
                    'economic': "Balanced spending on flood safety and community support",
                    'social': "Cooperative approach builds neighborly relations during crisis"
                },
                'c': {
                    'environmental': "Investment in flood-resistant housing reduces long-term vulnerability",
                    'economic': "Higher costs for flood-proofing but protection of property value",
                    'social': "Innovation adoption influences community flood preparedness standards"
                },
                'd': {
                    'environmental': "Limited flood preparation increases personal and community vulnerability",
                    'economic': "No preparation costs but risk of major flood damage and displacement",
                    'social': "Self-reliance approach may reduce community cooperation during emergencies"
                }
            },
            3: {  # Chennai Water Shortage
                'a': {
                    'environmental': "Household water conservation reduces city-wide consumption and waste",
                    'economic': "Lower water bills but lifestyle changes require adjustment and investment",
                    'social': "Conservation leadership inspires neighbors and builds community resilience"
                },
                'b': {
                    'environmental': "Water hoarding worsens scarcity for vulnerable populations without storage",
                    'economic': "Personal water security but higher costs and storage infrastructure needs",
                    'social': "Selfish behavior damages social fabric and community trust during crisis"
                },
                'c': {
                    'environmental': "Community water management reduces waste through shared monitoring",
                    'economic': "Collective action spreads costs and improves efficiency for all households",
                    'social': "Neighborhood cooperation builds lasting bonds and mutual support systems"
                },
                'd': {
                    'environmental': "Mass protests disrupt water management efforts and delay solutions",
                    'economic': "Political pressure may force expensive quick fixes over sustainable planning",
                    'social': "Public anger demands action but risks violence and polarization"
                }
            },
            4: {  # Migration & Heatwave
                'a': {
                    'environmental': "Migrant integration reduces urban inequality and builds climate-resilient communities",
                    'economic': "Volunteer time and resources stretch household budgets but build social capital",
                    'social': "Compassionate response strengthens urban social fabric and mutual aid networks"
                },
                'b': {
                    'environmental': "Exclusionary policies force migrants into polluted, vulnerable urban peripheries",
                    'economic': "Reduced competition for services but economic losses from restricted labor",
                    'social': "Anti-migrant stance hardens social divisions and creates inter-community tensions"
                },
                'c': {
                    'environmental': "Community kitchens reduce food waste and promote sustainable consumption",
                    'economic': "Shared cooking costs reduce individual expenses while supporting migrants",
                    'social': "Food sharing builds cross-community bonds and demonstrates urban hospitality"
                },
                'd': {
                    'environmental': "Rent protests may ignore environmental costs of urban sprawl and development",
                    'economic': "Housing cost activism benefits current residents but may worsen migration pressures",
                    'social': "Economic protests unite urban residents but may exclude migrant voices and needs"
                }
            },
            5: {  # National Election/Policy
                'a': {
                    'environmental': "Climate candidate support drives policy change toward renewable energy and conservation",
                    'economic': "Green transition may increase short-term costs but creates sustainable urban development",
                    'social': "Climate activism builds community engagement and youth political participation"
                },
                'b': {
                    'environmental': "Economic protest may delay climate action in favor of immediate economic relief",
                    'economic': "Focus on employment and costs but climate damages continue to mount",
                    'social': "Economic grievances legitimate but may overlook environmental justice concerns"
                },
                'c': {
                    'environmental': "Urban-rural climate cooperation addresses comprehensive environmental challenges",
                    'economic': "Inclusive approach spreads transition costs and benefits across communities",
                    'social': "Bridge-building reduces urban-rural polarization on climate policy"
                },
                'd': {
                    'environmental': "Demanding freebies may prioritize consumption over environmental sustainability",
                    'economic': "Short-term benefits popular but unsustainable fiscal and environmental costs",
                    'social': "Populist demands may undermine long-term climate action and social cohesion"
                }
            }
        },
        'ngo_worker': {
            1: {  # Delhi Air Pollution
                'a': {
                    'environmental': "Advocacy drives rapid policy implementation and community action",
                    'economic': "Grant funding increases for urgent environmental projects",
                    'social': "High visibility campaigns build public awareness and pressure"
                },
                'b': {
                    'environmental': "Balanced advocacy maintains momentum while building broader coalitions",
                    'economic': "Steady funding for long-term environmental programs",
                    'social': "Collaborative approach brings together diverse stakeholders"
                },
                'c': {
                    'environmental': "Innovation focus attracts tech partnerships and pilot projects",
                    'economic': "Private sector partnerships provide resources for scaling solutions",
                    'social': "Educational campaigns increase public understanding of technology solutions"
                },
                'd': {
                    'environmental': "Limited action means missed opportunity for environmental leadership",
                    'economic': "Reduced funding as donors seek more active organizations",
                    'social': "Stakeholder disappointment in NGO effectiveness and commitment"
                }
            },
            2: {  # Mumbai Floods
                'a': {
                    'environmental': "Emergency relief coordination minimizes flood damage and supports recovery",
                    'economic': "Increased emergency funding for immediate flood response and relief",
                    'social': "High-impact community service builds trust and demonstrates NGO effectiveness"
                },
                'b': {
                    'environmental': "Balanced relief and resilience building addresses immediate and long-term needs",
                    'economic': "Steady funding for comprehensive flood response and community preparation",
                    'social': "Collaborative approach brings together multiple stakeholders for flood management"
                },
                'c': {
                    'environmental': "Long-term flood resilience programs reduce future environmental damage",
                    'economic': "Grant funding for innovative flood adaptation and climate resilience projects",
                    'social': "Educational programs increase community awareness of flood risks and preparation"
                },
                'd': {
                    'environmental': "Limited flood response reduces NGO impact on environmental protection",
                    'economic': "Reduced funding as donors prioritize active emergency response organizations",
                    'social': "Community disappointment in NGO availability during crisis situations"
                }
            },
            3: {  # Chennai Water Shortage
                'a': {
                    'environmental': "Water education programs build long-term conservation behavior change",
                    'economic': "Education investment shows results slowly but creates sustained impact",
                    'social': "Community awareness reduces panic and builds collective action capacity"
                },
                'b': {
                    'environmental': "Policy advocacy addresses root causes of water mismanagement and waste",
                    'economic': "Structural change requires time but prevents recurring water crises",
                    'social': "Corporate and government accountability improves resource governance"
                },
                'c': {
                    'environmental': "Emergency water distribution prevents humanitarian crisis but not causes",
                    'economic': "Immediate relief funding maintains operations but limits long-term planning",
                    'social': "Crisis response builds NGO credibility and community trust"
                },
                'd': {
                    'environmental': "Infrastructure lobbying may create large projects but risks environmental damage",
                    'economic': "Mega-project funding attractive but uncertain implementation and corruption risks",
                    'social': "Big infrastructure promises may displace communities and worsen inequality"
                }
            },
            4: {  # Migration & Heatwave
                'a': {
                    'environmental': "Skills programs can include green jobs and climate adaptation training",
                    'economic': "Training investment builds human capital for sustainable economic transition",
                    'social': "Empowerment through education creates leadership and reduces dependency"
                },
                'b': {
                    'environmental': "Urban planning advocacy addresses root causes of climate vulnerability",
                    'economic': "Policy change requires sustained investment but creates systemic solutions",
                    'social': "Inclusive planning ensures migrant voices in urban development decisions"
                },
                'c': {
                    'environmental': "Industry partnerships may compromise environmental standards for employment",
                    'economic': "Corporate funding expands NGO capacity but may create conflicts of interest",
                    'social': "Business collaboration improves migrant employment but risks worker exploitation"
                },
                'd': {
                    'environmental': "Human rights monitoring documents environmental justice impacts of migration",
                    'economic': "Advocacy work requires sustained funding but builds case for policy change",
                    'social': "Rights protection ensures dignity but may create government backlash against NGO operations"
                }
            },
            5: {  # National Election/Policy
                'a': {
                    'environmental': "Coalition building creates powerful movement for comprehensive climate policy",
                    'economic': "United advocacy attracts more funding and influences business and government",
                    'social': "Grand coalition bridges divides but requires managing competing organizational interests"
                },
                'b': {
                    'environmental': "Local resilience pilots demonstrate practical solutions and build community capacity",
                    'economic': "Small-scale projects show cost-effective impact but limited to local areas",
                    'social': "Community-level success builds trust and replicable models for scaling"
                },
                'c': {
                    'environmental': "Pledge monitoring ensures accountability but may have limited enforcement power",
                    'economic': "Transparency work builds reputation but requires sustained operational funding",
                    'social': "Public information increases awareness but political impact depends on public engagement"
                },
                'd': {
                    'environmental': "Media campaigns raise awareness but impact fades without sustained follow-through",
                    'economic': "High visibility attracts short-term funding but may divert from core programs",
                    'social': "Public attention helpful but electoral focus may overshadow long-term relationship building"
                }
            }
        }
    }
    
    # Get specific reasoning for this option
    role_reasoning = reasoning_templates.get(role, {})
    scenario_reasoning = role_reasoning.get(scenario.round_number, {})
    option_reasoning = scenario_reasoning.get(option.option_letter, {
        'environmental': "Environmental impacts depend on specific implementation details",
        'economic': "Economic effects vary based on scale and execution of the decision",
        'social': "Social outcomes influenced by stakeholder engagement and communication"
    })
    
    # Add meter impact explanations
    meter_explanations = []
    for meter, value in option.outcome_logic.items():
        if value > 0:
            direction = "increases"
            icon = "📈"
        elif value < 0:
            direction = "decreases"
            icon = "📉"
        else:
            direction = "remains stable"
            icon = "➡️"
        
        meter_name = meter.replace('_', ' ').title()
        meter_explanations.append(f"{icon} {meter_name} {direction} by {abs(value)} points")
    
    return {
        'environmental': option_reasoning['environmental'],
        'economic': option_reasoning['economic'],
        'social': option_reasoning['social'],
        'meter_impacts': meter_explanations,
        'is_selected': is_selected
    }


def generate_learning_outcome(scenario, response_summary):
    """Generate key learning points for the round"""
    learning_outcomes = {
        1: "Climate action requires coordination across all stakeholders. Economic and environmental goals must be balanced through innovative policies.",
        2: "Urban resilience depends on both emergency response and long-term infrastructure planning. Community preparation is as important as government action.",
        3: "Water scarcity demands both conservation and sustainable resource management. Competition for resources can be resolved through cooperation.",
        4: "Climate migration requires compassionate policies that support both migrants and host communities. Adaptation must address root causes.",
        5: "Democratic processes can drive climate action when citizens, businesses, and government align on long-term thinking over short-term gains."
    }
    
    return learning_outcomes.get(scenario.round_number, 
        "Complex challenges require multi-stakeholder collaboration and long-term thinking.")


# Testing and Development Views

def create_test_climate_session(request):
    """
    Create a test session for single-player testing during development
    """
    try:
        climate_game = ClimateGame.objects.first()
        if not climate_game:
            messages.error(request, "No climate game available. Please run 'python manage.py populate_climate_scenarios' first.")
            return redirect('group_learning:climate_game_home')
        
        # Generate unique session code with TEST prefix
        session_code = f"TEST{random.randint(1000, 9999)}"
        
        # Create test session
        session = ClimateGameSession.objects.create(
            game=climate_game,  # Set the base game field (ClimateGame inherits from Game)
            climate_game=climate_game,
            session_code=session_code,
            current_phase='lobby',
            phase_start_time=timezone.now(),
            # Store test session metadata in session_data
            session_data={
                'session_name': f"Test Session - {timezone.now().strftime('%H:%M')}",
                'facilitator_name': 'Developer',
                'is_test_session': True,
                'auto_advance': True
            }
        )
        
        messages.success(request, f"Test session created! Code: {session_code}")
        return redirect('group_learning:climate_facilitator_dashboard', session_code=session_code)
        
    except Exception as e:
        messages.error(request, f"Error creating test session: {str(e)}")
        return redirect('group_learning:climate_game_home')


def quick_test_join(request, session_code, role=None):
    """
    Quick join test session with specified role or auto-assign
    """
    try:
        session = get_object_or_404(ClimateGameSession, session_code=session_code)
        
        # Available roles for testing
        available_roles = ['government', 'business', 'farmer', 'urban_citizen', 'ngo_worker']
        role_names = {
            'government': 'Gov Official',
            'business': 'Business Owner', 
            'farmer': 'Farmer',
            'urban_citizen': 'Urban Citizen',
            'ngo_worker': 'NGO Worker'
        }
        
        # Use specified role or assign first available
        if role and role in available_roles:
            assigned_role = role
        else:
            # Find existing players to avoid duplicates
            existing_roles = set(ClimatePlayerResponse.objects.filter(
                climate_session=session
            ).values_list('assigned_role', flat=True).distinct())
            
            available = [r for r in available_roles if r not in existing_roles]
            assigned_role = available[0] if available else available_roles[0]
        
        # Create player session
        player_session_id = f"test_{assigned_role}_{random.randint(100, 999)}"
        player_name = role_names[assigned_role]
        
        # Store in session
        request.session['player_session_id'] = player_session_id
        request.session['player_name'] = player_name
        request.session['player_role'] = assigned_role
        
        messages.success(request, f"Joined as {player_name} for testing!")
        
        # Redirect based on game phase
        if session.current_phase == 'lobby':
            return redirect('group_learning:climate_game_lobby', session_code=session_code)
        else:
            return redirect('group_learning:climate_game_play', session_code=session_code)
            
    except Exception as e:
        messages.error(request, f"Error joining test session: {str(e)}")
        return redirect('group_learning:climate_game_home')


# Timer API endpoints

@csrf_exempt
@require_http_methods(["POST"])
def set_timer_duration(request, session_code):
    """
    Facilitator sets timer duration for rounds
    """
    session = get_object_or_404(ClimateGameSession, session_code=session_code)
    
    try:
        duration_minutes = int(request.POST.get('duration', 5))
        if duration_minutes < 1 or duration_minutes > 30:
            return JsonResponse({'success': False, 'message': 'Duration must be between 1-30 minutes'})
        
        session.set_timer_duration(duration_minutes)
        
        return JsonResponse({
            'success': True,
            'duration': duration_minutes,
            'message': f'Timer duration set to {duration_minutes} minutes'
        })
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid duration value'})


@csrf_exempt
@require_http_methods(["POST"])
def start_round_timer(request, session_code):
    """
    Facilitator starts timer for current round
    """
    session = get_object_or_404(ClimateGameSession, session_code=session_code)
    
    try:
        duration_minutes = None
        
        # Handle both JSON and form data for backward compatibility
        if request.content_type == 'application/json':
            import json
            try:
                data = json.loads(request.body.decode('utf-8'))
                duration_minutes = data.get('duration')
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        else:
            # Fallback to form data
            duration_minutes = request.POST.get('duration')
        
        if duration_minutes:
            duration_minutes = int(duration_minutes)
            session.start_timer(duration_minutes)
        else:
            session.start_timer()
        
        timer_info = session.get_timer_info()
        
        # Broadcast timer started via WebSocket
        from .websocket_utils import broadcast_timer_started
        broadcast_timer_started(session_code, timer_info)
        
        return JsonResponse({
            'success': True,
            'timer_info': timer_info,
            'message': 'Timer started'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def get_timer_status(request, session_code):
    """
    Get current timer status for session
    """
    session = get_object_or_404(ClimateGameSession, session_code=session_code)
    timer_info = session.get_timer_info()
    
    return JsonResponse({
        'success': True,
        'timer_info': timer_info,
        'round_duration_minutes': session.round_duration_minutes
    })