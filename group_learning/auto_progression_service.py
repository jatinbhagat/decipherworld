"""
Auto-progression service for simplified Design Thinking sessions
Handles phase completion detection and automatic advancement logic
"""

import logging
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    DesignThinkingSession, DesignTeam, DesignMission, 
    SimplifiedPhaseInput, PhaseCompletionTracker, TeamProgress
)
from .monitoring import (
    log_operation, log_session_activity, log_error, performance_monitor
)

logger = logging.getLogger(__name__)


class AutoProgressionService:
    """
    Service class for handling auto-progression logic in simplified Design Thinking sessions
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    @log_operation('process_phase_input')
    def process_phase_input(self, team_id, mission_id, student_data, input_data):
        """
        Process a simplified phase input and check for auto-progression
        Returns dict with progression status and next steps
        """
        # Input validation
        validation_result = self._validate_input_data(team_id, mission_id, student_data, input_data)
        if not validation_result['valid']:
            return {
                'success': False, 
                'error': f"Input validation failed: {validation_result['error']}"
            }
        
        try:
            with transaction.atomic():
                # Save the input with enhanced validation
                phase_input = self._save_phase_input(team_id, mission_id, student_data, input_data)
                
                if not phase_input:
                    log_error('input_save_failed', phase_input.session.session_code if phase_input else None, {
                        'team_id': team_id,
                        'mission_id': mission_id
                    })
                    return {
                        'success': False, 
                        'error': 'Failed to save input - database error',
                        'retry_allowed': True
                    }
                
                # Update completion tracking
                completion_result = self._update_completion_tracking(phase_input)
                
                # Check for auto-progression
                progression_result = self._check_auto_progression(phase_input.team, phase_input.mission)
                
                # Broadcast updates via WebSocket (with error handling)
                broadcast_success = self._broadcast_input_update(phase_input, completion_result, progression_result)
                
                # Log successful input processing
                log_session_activity(
                    phase_input.session.session_code,
                    'input_processed',
                    {
                        'team_id': team_id,
                        'mission_id': mission_id,
                        'student_name': student_data.get('name', 'Unknown'),
                        'input_count': len(input_data),
                        'completion_percentage': completion_result.get('completion_percentage', 0),
                        'auto_advance_triggered': progression_result.get('should_advance', False)
                    }
                )
                
                return {
                    'success': True,
                    'input_saved': True,
                    'completion_result': completion_result,
                    'progression_result': progression_result,
                    'broadcast_success': broadcast_success,
                    'phase_input_id': phase_input.id
                }
                
        except ValidationError as e:
            logger.warning(f"Validation error processing phase input: {str(e)}")
            log_error('validation_error', None, {
                'team_id': team_id,
                'mission_id': mission_id,
                'error_message': str(e)
            })
            return {
                'success': False, 
                'error': f'Validation error: {str(e)}',
                'retry_allowed': False
            }
        except Exception as e:
            logger.error(f"Unexpected error processing phase input: {str(e)}", exc_info=True)
            log_error('phase_input_processing_error', None, {
                'team_id': team_id,
                'mission_id': mission_id,
                'error_message': str(e),
                'error_type': type(e).__name__
            })
            return {
                'success': False, 
                'error': 'Internal server error occurred',
                'retry_allowed': True,
                'debug_info': str(e) if getattr(settings, 'DEBUG', False) else None
            }
    
    def _validate_input_data(self, team_id, mission_id, student_data, input_data):
        """Comprehensive input validation before processing"""
        try:
            # Basic parameter validation
            if not all([team_id, mission_id, student_data, input_data]):
                return {'valid': False, 'error': 'Missing required parameters'}
            
            # Team validation
            try:
                team = DesignTeam.objects.get(id=team_id)
            except DesignTeam.DoesNotExist:
                return {'valid': False, 'error': f'Team {team_id} not found'}
            
            # Mission validation
            try:
                mission = DesignMission.objects.get(id=mission_id)
            except DesignMission.DoesNotExist:
                return {'valid': False, 'error': f'Mission {mission_id} not found'}
            
            # Session consistency validation
            if team.session.design_game != mission.game:
                return {'valid': False, 'error': 'Team and mission belong to different games'}
            
            # Student data validation
            if not isinstance(student_data, dict):
                return {'valid': False, 'error': 'Student data must be a dictionary'}
            
            student_name = student_data.get('name', '').strip()
            student_session_id = student_data.get('session_id', '').strip()
            
            if not student_name or len(student_name) > 100:
                return {'valid': False, 'error': 'Valid student name (1-100 chars) required'}
            
            if not student_session_id or len(student_session_id) > 100:
                return {'valid': False, 'error': 'Valid student session ID (1-100 chars) required'}
            
            # Input data validation
            if not isinstance(input_data, list) or len(input_data) == 0:
                return {'valid': False, 'error': 'Input data must be a non-empty list'}
            
            if len(input_data) > 10:
                return {'valid': False, 'error': 'Too many inputs (max 10 per submission)'}
            
            # Validate each input
            for i, input_item in enumerate(input_data):
                if not isinstance(input_item, dict):
                    return {'valid': False, 'error': f'Input {i+1} must be a dictionary'}
                
                input_type = input_item.get('type', '')
                input_label = input_item.get('label', '').strip()
                input_value = input_item.get('value', '').strip()
                
                if input_type not in ['radio', 'dropdown', 'checkbox', 'text_short', 'text_medium', 'rating']:
                    return {'valid': False, 'error': f'Invalid input type: {input_type}'}
                
                if not input_label or len(input_label) > 200:
                    return {'valid': False, 'error': f'Input {i+1} label must be 1-200 characters'}
                
                if not input_value or len(input_value) > 500:
                    return {'valid': False, 'error': f'Input {i+1} value must be 1-500 characters'}
                
                # Type-specific validation
                if input_type == 'text_short' and len(input_value) > 50:
                    return {'valid': False, 'error': f'Short text input {i+1} cannot exceed 50 characters'}
                elif input_type == 'text_medium' and len(input_value) > 200:
                    return {'valid': False, 'error': f'Medium text input {i+1} cannot exceed 200 characters'}
                elif input_type == 'rating':
                    try:
                        rating = int(input_value)
                        if not 1 <= rating <= 5:
                            return {'valid': False, 'error': f'Rating {i+1} must be between 1 and 5'}
                    except ValueError:
                        return {'valid': False, 'error': f'Rating {i+1} must be a valid number'}
            
            # Check for duplicate submissions
            existing_inputs = SimplifiedPhaseInput.objects.filter(
                team=team,
                mission=mission,
                student_session_id=student_session_id,
                is_active=True
            ).count()

            if existing_inputs > 0:
                return {'valid': False, 'error': 'Student has already submitted inputs for this phase'}

            # PREVENT BACKWARD NAVIGATION: Check if team is trying to submit for an earlier phase
            session = team.session
            current_mission = session.current_mission
            if current_mission and mission.order < current_mission.order:
                return {
                    'valid': False,
                    'error': f'Cannot submit for past phase. Current phase is {current_mission.mission_type}.'
                }

            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating input data: {str(e)}")
            return {'valid': False, 'error': 'Validation system error'}
    
    def _save_phase_input(self, team_id, mission_id, student_data, input_data):
        """Save simplified phase input to database"""
        try:
            team = DesignTeam.objects.get(id=team_id)
            mission = DesignMission.objects.get(id=mission_id)
            session = team.session
            
            # Create input records for each input submitted
            phase_inputs = []
            for input_item in input_data:
                phase_input = SimplifiedPhaseInput.objects.create(
                    team=team,
                    mission=mission,
                    session=session,
                    student_name=student_data.get('name', 'Anonymous'),
                    student_session_id=student_data.get('session_id'),
                    input_type=input_item.get('type'),
                    input_label=input_item.get('label'),
                    selected_value=input_item.get('value'),
                    input_order=input_item.get('order', 1),
                    time_to_complete_seconds=input_item.get('time_taken', 0)
                )
                phase_inputs.append(phase_input)
            
            logger.info(f"✅ Saved {len(phase_inputs)} phase inputs for team {team.team_name}")
            return phase_inputs[0] if phase_inputs else None  # Return first input for further processing
            
        except Exception as e:
            logger.error(f"Error saving phase input: {str(e)}")
            return None
    
    def _update_completion_tracking(self, phase_input):
        """Update completion tracking for the team's current phase"""
        try:
            team = phase_input.team
            mission = phase_input.mission
            session = phase_input.session
            
            # Get or create completion tracker
            tracker, created = PhaseCompletionTracker.objects.get_or_create(
                session=session,
                team=team,
                mission=mission,
                defaults={
                    'total_required_inputs': self._calculate_required_inputs(mission, team),
                    'completed_inputs': 0
                }
            )
            
            if created:
                logger.info(f"📊 Created new completion tracker for {team.team_name} - {mission.title}")
            
            # Increment completed inputs
            tracker.completed_inputs += 1
            is_ready = tracker.update_completion_status()
            
            # Update team progress model as well
            team_progress, _ = TeamProgress.objects.get_or_create(
                session=session,
                team=team,
                mission=mission,
                defaults={'started_at': timezone.now()}
            )
            
            if is_ready and not team_progress.is_completed:
                team_progress.mark_completed()
            
            logger.info(f"📈 Updated completion: {team.team_name} - {tracker.completion_percentage}% complete")
            
            return {
                'completion_percentage': tracker.completion_percentage,
                'is_ready_to_advance': tracker.is_ready_to_advance,
                'completed_inputs': tracker.completed_inputs,
                'total_required_inputs': tracker.total_required_inputs
            }
            
        except Exception as e:
            logger.error(f"Error updating completion tracking: {str(e)}")
            return {
                'completion_percentage': 0,
                'is_ready_to_advance': False,
                'completed_inputs': 0,
                'total_required_inputs': 1
            }
    
    def _check_auto_progression(self, team, mission):
        """Check if auto-progression should be triggered"""
        try:
            session = team.session
            
            # Check if auto-progression is enabled
            if not session.design_game.auto_advance_enabled:
                return {'should_advance': False, 'reason': 'Auto-progression disabled'}
            
            # Get completion tracker for this team
            try:
                tracker = PhaseCompletionTracker.objects.get(
                    session=session,
                    team=team,
                    mission=mission
                )
            except PhaseCompletionTracker.DoesNotExist:
                return {'should_advance': False, 'reason': 'No completion tracker found'}
            
            if not tracker.is_ready_to_advance:
                return {'should_advance': False, 'reason': 'Team not ready to advance'}
            
            # Check session-wide advancement requirements
            advancement_result = self._check_session_advancement_requirements(session, mission)
            
            if advancement_result['should_advance']:
                # Get next mission
                next_mission = self._get_next_mission(session, mission)
                if next_mission:
                    advancement_result.update({
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
                    advancement_result['should_advance'] = False
                    advancement_result['reason'] = 'No next mission available'
            
            return advancement_result
            
        except Exception as e:
            logger.error(f"Error checking auto-progression: {str(e)}")
            return {'should_advance': False, 'reason': f'Error: {str(e)}'}
    
    def _check_session_advancement_requirements(self, session, mission):
        """Check if session-wide requirements are met for advancement"""
        try:
            # Get all teams in session
            total_teams = session.design_teams.count()
            if total_teams == 0:
                return {'should_advance': False, 'reason': 'No teams in session'}
            
            # Count teams ready to advance for this mission
            ready_teams = PhaseCompletionTracker.objects.filter(
                session=session,
                mission=mission,
                is_ready_to_advance=True
            ).count()
            
            # Calculate percentage of teams ready
            ready_percentage = (ready_teams / total_teams) * 100
            required_percentage = session.design_game.completion_threshold_percentage
            
            logger.info(f"🎯 Advancement check: {ready_teams}/{total_teams} teams ready ({ready_percentage}%), required: {required_percentage}%")
            
            if ready_percentage >= required_percentage:
                return {
                    'should_advance': True,
                    'ready_teams': ready_teams,
                    'total_teams': total_teams,
                    'ready_percentage': ready_percentage,
                    'required_percentage': required_percentage
                }
            else:
                return {
                    'should_advance': False,
                    'reason': f'Only {ready_percentage}% of teams ready, need {required_percentage}%',
                    'ready_teams': ready_teams,
                    'total_teams': total_teams,
                    'ready_percentage': ready_percentage
                }
            
        except Exception as e:
            logger.error(f"Error checking session advancement requirements: {str(e)}")
            return {'should_advance': False, 'reason': f'Error: {str(e)}'}
    
    def _get_next_mission(self, session, current_mission):
        """Get the next mission in sequence"""
        try:
            next_mission = DesignMission.objects.filter(
                game=session.design_game,
                order=current_mission.order + 1,
                is_active=True
            ).first()
            return next_mission
        except Exception as e:
            logger.error(f"Error getting next mission: {str(e)}")
            return None
    
    def _calculate_required_inputs(self, mission, team):
        """Calculate total required inputs for team to complete mission"""
        try:
            # Get input schema from mission
            input_schema = mission.input_schema or {}
            inputs_per_person = len(input_schema.get('inputs', [])) if input_schema else 1
            
            # If no schema defined, use default based on mission type
            if inputs_per_person == 0:
                defaults = {
                    'empathy': 2,    # 2 radio button questions
                    'define': 2,     # 1 dropdown + 1 text input
                    'ideate': 4,     # 3 text inputs + 1 radio selection
                    'prototype': 2,  # 1 text area + 1 checkbox
                    'showcase': 2    # 2 rating inputs
                }
                inputs_per_person = defaults.get(mission.mission_type, 1)
            
            # Calculate based on team requirements
            if mission.requires_all_team_members:
                team_size = len(team.team_members) if team.team_members else 1
                total_required = team_size * inputs_per_person
            else:
                total_required = inputs_per_person  # Only one team member needs to complete
            
            logger.info(f"📊 Required inputs for {team.team_name} - {mission.title}: {total_required}")
            return total_required
            
        except Exception as e:
            logger.error(f"Error calculating required inputs: {str(e)}")
            return 1  # Default fallback
    
    def _broadcast_input_update(self, phase_input, completion_result, progression_result):
        """Broadcast input submission update via WebSocket"""
        try:
            if not self.channel_layer:
                logger.warning("No channel layer available for broadcasting")
                return False
            
            session_code = phase_input.session.session_code
            room_group_name = f'design_thinking_{session_code}'
            
            # Prepare team data
            team_data = {
                'id': phase_input.team.id,
                'name': phase_input.team.team_name,
                'emoji': phase_input.team.team_emoji
            }
            
            # Prepare input data  
            input_data = [{
                'type': phase_input.input_type,
                'label': phase_input.input_label,
                'value': phase_input.selected_value,
                'order': phase_input.input_order
            }]
            
            # Send input submission update
            async_to_sync(self.channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'input_submission_update',
                    'team_data': team_data,
                    'input_data': input_data,
                    'auto_advance_result': progression_result,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Send completion status update
            async_to_sync(self.channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'completion_status_update',
                    'team_data': team_data,
                    'completion_percentage': completion_result['completion_percentage'],
                    'is_ready_to_advance': completion_result['is_ready_to_advance'],
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            logger.info(f"📡 Broadcasted input update for {phase_input.team.team_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error broadcasting input update: {str(e)}")
            return False
    
    def execute_auto_advancement(self, session_code, current_mission_id, next_mission_id):
        """Execute the actual auto-advancement to next phase"""
        try:
            with transaction.atomic():
                session = DesignThinkingSession.objects.get(session_code=session_code)
                next_mission = DesignMission.objects.get(id=next_mission_id)
                
                # Update session current mission
                session.current_mission = next_mission
                session.mission_start_time = timezone.now()
                session.save()
                
                # Reset completion tracking for all teams for the new mission
                PhaseCompletionTracker.objects.filter(
                    session=session,
                    mission_id=next_mission_id
                ).delete()  # Clean slate for new phase
                
                # Broadcast mission advancement
                if self.channel_layer:
                    room_group_name = f'design_thinking_{session_code}'
                    mission_data = {
                        'id': next_mission.id,
                        'title': next_mission.title,
                        'mission_type': next_mission.mission_type,
                        'description': next_mission.description,
                        'instructions': getattr(next_mission, 'instructions', '')
                    }
                    
                    async_to_sync(self.channel_layer.group_send)(
                        room_group_name,
                        {
                            'type': 'mission_advanced',
                            'mission_data': mission_data,
                            'timestamp': timezone.now().isoformat()
                        }
                    )
                
                logger.info(f"🎯 Successfully advanced session {session_code} to {next_mission.title}")
                return True
                
        except Exception as e:
            logger.error(f"Error executing auto-advancement: {str(e)}")
            return False
    
    @log_operation('save_teacher_score')
    def save_teacher_score(self, team_id, mission_id, score, teacher_id):
        """Save teacher score for a team's phase completion"""
        try:
            with transaction.atomic():
                team = DesignTeam.objects.get(id=team_id)
                mission = DesignMission.objects.get(id=mission_id)
                
                # Update all inputs from this team for this mission
                updated_count = SimplifiedPhaseInput.objects.filter(
                    team=team,
                    mission=mission,
                    teacher_score__isnull=True
                ).update(
                    teacher_score=score,
                    scored_at=timezone.now()
                )
                
                # Broadcast score update
                if self.channel_layer:
                    session_code = team.session.session_code
                    room_group_name = f'design_thinking_{session_code}'
                    
                    async_to_sync(self.channel_layer.group_send)(
                        room_group_name,
                        {
                            'type': 'teacher_score_update',
                            'team_data': {
                                'id': team.id,
                                'name': team.team_name,
                                'emoji': team.team_emoji
                            },
                            'mission_data': {
                                'id': mission.id,
                                'title': mission.title,
                                'mission_type': mission.mission_type
                            },
                            'score': score,
                            'timestamp': timezone.now().isoformat()
                        }
                    )
                
                logger.info(f"📊 Saved teacher score for {team.team_name} - {mission.title}: {score} (updated {updated_count} inputs)")
                
                # Log teacher scoring activity
                log_session_activity(
                    team.session.session_code,
                    'teacher_scored',
                    {
                        'team_id': team_id,
                        'team_name': team.team_name,
                        'mission_id': mission_id,
                        'mission_title': mission.title,
                        'score': score,
                        'inputs_updated': updated_count,
                        'teacher_id': teacher_id
                    }
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error saving teacher score: {str(e)}")
            return False


# Global service instance
auto_progression_service = AutoProgressionService()