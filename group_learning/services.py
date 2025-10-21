"""
Design Thinking Game Services
Centralized business logic for mission advancement, progress tracking, and session management
"""

from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from .cache import DesignThinkingCache

from .models import (
    DesignThinkingSession, DesignTeam, TeamProgress, 
    TeamSubmission, DesignMission, DesignThinkingGame
)

logger = logging.getLogger(__name__)


class MissionAdvancementError(Exception):
    """Custom exception for mission advancement issues"""
    pass


class DesignThinkingService:
    """
    Centralized service for Design Thinking game operations
    Handles mission advancement, progress tracking, and real-time updates
    """
    
    def __init__(self, session):
        """
        Initialize service for a specific session
        
        Args:
            session: DesignThinkingSession instance
        """
        if not isinstance(session, DesignThinkingSession):
            raise ValueError("Session must be a DesignThinkingSession instance")
        
        self.session = session
        self.channel_layer = get_channel_layer()
    
    def advance_to_mission(self, mission_order):
        """
        Advance session to a specific mission with atomic transaction
        
        Args:
            mission_order (int): Order of the mission to advance to (1-6)
            
        Returns:
            dict: Result with success status and mission details
            
        Raises:
            MissionAdvancementError: If advancement fails
        """
        try:
            with transaction.atomic():
                # Validate mission order
                if not (1 <= mission_order <= 6):
                    raise MissionAdvancementError(f"Invalid mission order: {mission_order}. Must be 1-6.")
                
                # Get target mission
                target_mission = DesignMission.objects.filter(
                    game=self.session.design_game,
                    order=mission_order,
                    is_active=True
                ).first()
                
                if not target_mission:
                    raise MissionAdvancementError(f"Mission with order {mission_order} not found or inactive")
                
                # Update session mission state
                old_mission = self.session.current_mission
                self.session.current_mission = target_mission
                self.session.mission_start_time = timezone.now()
                self.session.mission_end_time = None
                self.session.status = 'in_progress'
                self.session.save()
                
                # Create/update TeamProgress records for all teams
                teams = self.session.design_teams.all()
                progress_created = 0
                
                for team in teams:
                    # Create progress records for all missions up to current
                    missions_to_create = DesignMission.objects.filter(
                        game=self.session.design_game,
                        order__lte=mission_order,
                        is_active=True
                    )
                    
                    for mission in missions_to_create:
                        progress, created = TeamProgress.objects.get_or_create(
                            session=self.session,
                            team=team,
                            mission=mission,
                            defaults={
                                'started_at': timezone.now() if mission == target_mission else None,
                                'is_completed': mission.order < mission_order  # Previous missions are completed
                            }
                        )
                        
                        if created:
                            progress_created += 1
                            logger.info(f"Created TeamProgress for {team.team_name} - {mission.title}")
                
                # Remove any progress records for future missions (cleanup)
                future_missions = DesignMission.objects.filter(
                    game=self.session.design_game,
                    order__gt=mission_order,
                    is_active=True
                )
                
                deleted_count = TeamProgress.objects.filter(
                    session=self.session,
                    mission__in=future_missions
                ).delete()[0]
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} future mission progress records")
                
                # Invalidate caches after mission advancement
                DesignThinkingCache.invalidate_all_session_caches(self.session.session_code)
                
                # Broadcast real-time updates
                self._broadcast_mission_change(old_mission, target_mission)
                
                return {
                    'success': True,
                    'message': f'Advanced to {target_mission.title}',
                    'mission': {
                        'id': target_mission.id,
                        'title': target_mission.title,
                        'order': target_mission.order,
                        'description': target_mission.description
                    },
                    'progress_created': progress_created,
                    'future_cleaned': deleted_count
                }
                
        except Exception as e:
            logger.error(f"Mission advancement failed for session {self.session.session_code}: {str(e)}")
            raise MissionAdvancementError(f"Failed to advance to mission {mission_order}: {str(e)}")
    
    def advance_to_next_mission(self):
        """
        Advance to the next mission in sequence
        
        Returns:
            dict: Result from advance_to_mission()
        """
        current_order = 0
        if self.session.current_mission:
            current_order = self.session.current_mission.order
        
        next_order = current_order + 1
        
        if next_order > 6:
            raise MissionAdvancementError("Already at the final mission")
        
        return self.advance_to_mission(next_order)
    
    def complete_current_mission(self, team=None):
        """
        Mark current mission as completed for a team or all teams
        
        Args:
            team: Specific DesignTeam instance, or None for all teams
            
        Returns:
            dict: Completion result
        """
        if not self.session.current_mission:
            raise MissionAdvancementError("No current mission to complete")
        
        try:
            with transaction.atomic():
                if team:
                    teams = [team]
                else:
                    teams = self.session.design_teams.all()
                
                completed_count = 0
                
                for team_obj in teams:
                    progress, created = TeamProgress.objects.get_or_create(
                        session=self.session,
                        team=team_obj,
                        mission=self.session.current_mission
                    )
                    
                    if not progress.is_completed:
                        progress.is_completed = True
                        progress.completed_at = timezone.now()
                        progress.save()
                        completed_count += 1
                
                # Broadcast completion updates
                self._broadcast_progress_update()
                
                return {
                    'success': True,
                    'message': f'Completed {self.session.current_mission.title}',
                    'teams_completed': completed_count
                }
                
        except Exception as e:
            logger.error(f"Mission completion failed: {str(e)}")
            raise MissionAdvancementError(f"Failed to complete mission: {str(e)}")
    
    def get_session_progress(self):
        """
        Get comprehensive progress data for the session with caching
        
        Returns:
            dict: Progress summary with mission states and team progress
        """
        # Try to get from cache first
        cached_data = DesignThinkingCache.get_session_progress(self.session.session_code)
        if cached_data:
            logger.debug(f"Returning cached progress data for session {self.session.session_code}")
            return cached_data
        
        logger.debug(f"Computing fresh progress data for session {self.session.session_code}")
        
        missions = DesignMission.objects.filter(
            game=self.session.design_game,
            is_active=True
        ).order_by('order')
        
        teams = self.session.design_teams.all()
        
        current_mission_order = 0
        if self.session.current_mission:
            current_mission_order = self.session.current_mission.order
        
        mission_progress = []
        
        for mission in missions:
            # Get team progress for this mission
            team_progress = TeamProgress.objects.filter(
                session=self.session,
                mission=mission
            ).select_related('team')
            
            # Determine mission state
            if mission.order < current_mission_order:
                state = 'completed'
            elif mission.order == current_mission_order:
                state = 'active'
            else:
                state = 'locked'
            
            # Count submissions for this mission with caching
            cached_count = DesignThinkingCache.get_team_submissions_count(
                'all_teams', mission.id
            )
            
            if cached_count is not None:
                submission_count = cached_count
            else:
                submission_count = TeamSubmission.objects.filter(
                    mission=mission,
                    team__in=teams
                ).count()
                
                # Cache the count
                DesignThinkingCache.set_team_submissions_count(
                    'all_teams', mission.id, submission_count
                )
            
            mission_progress.append({
                'id': mission.id,
                'title': mission.title,
                'order': mission.order,
                'state': state,
                'description': mission.description,
                'team_progress': [
                    {
                        'team_name': tp.team.team_name,
                        'is_completed': tp.is_completed,
                        'started_at': tp.started_at,
                        'completed_at': tp.completed_at
                    }
                    for tp in team_progress
                ],
                'submission_count': submission_count
            })
        
        progress_data = {
            'session_code': self.session.session_code,
            'current_mission': {
                'id': self.session.current_mission.id if self.session.current_mission else None,
                'title': self.session.current_mission.title if self.session.current_mission else None,
                'order': current_mission_order
            },
            'missions': mission_progress,
            'teams_count': teams.count(),
            'session_status': self.session.status
        }
        
        # Cache the computed data
        DesignThinkingCache.set_session_progress(self.session.session_code, progress_data)
        
        return progress_data
    
    def _broadcast_mission_change(self, old_mission, new_mission):
        """
        Broadcast mission change to all connected clients
        
        Args:
            old_mission: Previous DesignMission or None
            new_mission: New DesignMission
        """
        if not self.channel_layer:
            logger.warning("Channel layer not available for broadcasting")
            return
        
        message = {
            'type': 'mission_update',
            'mission': {
                'id': new_mission.id,
                'title': new_mission.title,
                'order': new_mission.order,
                'description': new_mission.description
            },
            'previous_mission': {
                'id': old_mission.id if old_mission else None,
                'title': old_mission.title if old_mission else None,
                'order': old_mission.order if old_mission else 0
            },
            'timestamp': timezone.now().isoformat()
        }
        
        # Broadcast to session group
        group_name = f"session_{self.session.session_code}"
        
        try:
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    'type': 'broadcast_message',
                    'message': message
                }
            )
            logger.info(f"Broadcasted mission change to group {group_name}")
        except Exception as e:
            logger.error(f"Failed to broadcast mission change: {str(e)}")
    
    def _broadcast_progress_update(self):
        """
        Broadcast progress update to all connected clients
        """
        if not self.channel_layer:
            return
        
        progress_data = self.get_session_progress()
        
        message = {
            'type': 'progress_update',
            'progress': progress_data,
            'timestamp': timezone.now().isoformat()
        }
        
        group_name = f"session_{self.session.session_code}"
        
        try:
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    'type': 'broadcast_message',
                    'message': message
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast progress update: {str(e)}")


class SubmissionService:
    """
    Service for handling team submissions with validation
    """
    
    @staticmethod
    def create_submission(team, mission, submission_type, content, title=None, uploaded_file=None):
        """
        Create a team submission with proper validation
        
        Args:
            team: DesignTeam instance
            mission: DesignMission instance
            submission_type: Type of submission ('observation', 'idea', etc.)
            content: Submission content
            title: Optional submission title
            uploaded_file: Optional uploaded file
            
        Returns:
            TeamSubmission: Created submission
        """
        try:
            with transaction.atomic():
                submission = TeamSubmission.objects.create(
                    team=team,
                    mission=mission,
                    submission_type=submission_type,
                    title=title or f"{submission_type.title()} from {team.team_name}",
                    content=content,
                    uploaded_file=uploaded_file,
                    file_type=None,  # Use None instead of empty string
                    submitted_by=f"Team {team.team_name}",
                    submitted_at=timezone.now()
                )
                
                # Check if this submission completes the mission for the team
                if mission.title == "Empathy" and submission_type == 'observation':
                    # Count total observations for this team
                    obs_count = TeamSubmission.objects.filter(
                        team=team,
                        mission=mission,
                        submission_type='observation'
                    ).count()
                    
                    # Complete mission if 5+ observations
                    if obs_count >= 5:
                        progress = TeamProgress.objects.filter(
                            team=team,
                            mission=mission
                        ).first()
                        
                        if progress and not progress.is_completed:
                            progress.is_completed = True
                            progress.completed_at = timezone.now()
                            progress.save()
                
                # Invalidate submission count caches
                DesignThinkingCache.invalidate_team_submissions(team.id, mission.id)
                DesignThinkingCache.invalidate_team_submissions('all_teams', mission.id)
                
                # Invalidate session progress cache as submission counts changed
                if hasattr(team, 'session') and team.session:
                    DesignThinkingCache.invalidate_session_progress(team.session.session_code)
                
                logger.info(f"Created submission for {team.team_name} - {mission.title}")
                return submission
                
        except Exception as e:
            logger.error(f"Submission creation failed: {str(e)}")
            raise ValidationError(f"Failed to create submission: {str(e)}")