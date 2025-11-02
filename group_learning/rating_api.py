"""
Rating API endpoints for Design Thinking Teacher Dashboard
"""

import json
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg, Count, Q
from django.db import transaction

from .models import (
    DesignThinkingSession, DesignTeam, DesignMission, 
    TeamPhaseRating, SimplifiedPhaseInput
)
from .consumers import DesignThinkingConsumer

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class TeamRatingAPIView(View):
    """Handle team rating CRUD operations"""
    
    def post(self, request, session_code):
        """Create or update a team rating"""
        try:
            data = json.loads(request.body)
            team_id = data.get('team_id')
            mission_type = data.get('mission_type')
            rating = data.get('rating')
            feedback = data.get('feedback', '')
            quick_notes = data.get('quick_notes', '')
            
            # Validate input
            if not all([team_id, mission_type, rating]):
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields: team_id, mission_type, rating'
                }, status=400)
            
            if not (1 <= int(rating) <= 5):
                return JsonResponse({
                    'success': False,
                    'error': 'Rating must be between 1 and 5'
                }, status=400)
            
            # Get objects
            session = get_object_or_404(DesignThinkingSession, session_code=session_code)
            team = get_object_or_404(DesignTeam, id=team_id, session=session)
            mission = get_object_or_404(DesignMission, 
                                      game=session.design_game, 
                                      mission_type=mission_type)
            
            # Get latest submission data for context
            latest_submission = team.phase_inputs.filter(
                mission=mission
            ).order_by('-submitted_at').first()
            
            submission_data = {}
            submission_summary = ""
            
            if latest_submission:
                submission_data = latest_submission.input_data
                submission_summary = self._generate_submission_summary(
                    mission_type, latest_submission.input_data
                )
            
            # Create or update rating
            with transaction.atomic():
                rating_obj, created = TeamPhaseRating.objects.update_or_create(
                    team=team,
                    mission=mission,
                    defaults={
                        'session': session,
                        'teacher': request.user,
                        'rating': int(rating),
                        'feedback': feedback,
                        'quick_notes': quick_notes,
                        'submission_data': submission_data,
                        'submission_summary': submission_summary,
                    }
                )
            
            # Broadcast update via WebSocket
            self._broadcast_rating_update(session_code, team, mission_type, rating_obj)
            
            return JsonResponse({
                'success': True,
                'rating': {
                    'id': rating_obj.id,
                    'rating': rating_obj.rating,
                    'rating_stars': rating_obj.rating_stars,
                    'feedback': rating_obj.feedback,
                    'quick_notes': rating_obj.quick_notes,
                    'rated_at': rating_obj.rated_at.isoformat(),
                    'is_new': created
                },
                'team_average': team.average_rating
            })
            
        except Exception as e:
            logger.error(f"Error saving team rating: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Failed to save rating'
            }, status=500)
    
    def get(self, request, session_code):
        """Get ratings for session or specific team"""
        try:
            session = get_object_or_404(DesignThinkingSession, session_code=session_code)
            team_id = request.GET.get('team_id')
            mission_type = request.GET.get('mission_type')
            
            # Base queryset
            ratings = TeamPhaseRating.objects.filter(session=session)
            
            # Filter by team if specified
            if team_id:
                ratings = ratings.filter(team_id=team_id)
            
            # Filter by mission type if specified
            if mission_type:
                ratings = ratings.filter(mission__mission_type=mission_type)
            
            # Serialize ratings
            ratings_data = []
            for rating in ratings.select_related('team', 'mission', 'teacher'):
                ratings_data.append({
                    'id': rating.id,
                    'team_id': rating.team.id,
                    'team_name': rating.team.team_name,
                    'mission_type': rating.mission.mission_type,
                    'mission_title': rating.mission.title,
                    'rating': rating.rating,
                    'rating_stars': rating.rating_stars,
                    'rating_description': rating.rating_description,
                    'feedback': rating.feedback,
                    'quick_notes': rating.quick_notes,
                    'submission_summary': rating.submission_summary,
                    'rated_at': rating.rated_at.isoformat(),
                    'teacher_name': rating.teacher.get_full_name() or rating.teacher.username,
                    'is_final': rating.is_final
                })
            
            return JsonResponse({
                'success': True,
                'ratings': ratings_data,
                'count': len(ratings_data)
            })
            
        except Exception as e:
            logger.error(f"Error fetching ratings: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Failed to fetch ratings'
            }, status=500)
    
    def _generate_submission_summary(self, mission_type, input_data):
        """Generate human-readable summary of submission"""
        if not input_data:
            return "No submission data"
        
        try:
            if mission_type == 'empathy':
                pain_points = [
                    inp.get('value', '') for inp in input_data 
                    if 'pain point' in inp.get('label', '').lower() and inp.get('value', '').strip()
                ]
                return f"Selected {len(pain_points)} pain points: {', '.join(pain_points[:3])}{'...' if len(pain_points) > 3 else ''}"
            
            elif mission_type == 'define':
                hmw = next((
                    inp.get('value', '') for inp in input_data 
                    if 'how might we' in inp.get('label', '').lower()
                ), '')
                return hmw[:200] + '...' if len(hmw) > 200 else hmw
            
            elif mission_type == 'ideate':
                ideas = [
                    inp.get('value', '') for inp in input_data 
                    if 'idea' in inp.get('label', '').lower() and inp.get('value', '').strip()
                ]
                favorite = next((
                    inp.get('value', '') for inp in input_data 
                    if 'favorite' in inp.get('label', '').lower()
                ), '')
                return f"Generated {len(ideas)} ideas. Favorite: {favorite}"
            
            elif mission_type == 'prototype':
                prototype = next((
                    inp.get('value', '') for inp in input_data 
                    if 'prototype' in inp.get('label', '').lower()
                ), '')
                return prototype[:200] + '...' if len(prototype) > 200 else prototype
            
            return f"Completed {len(input_data)} inputs"
            
        except Exception as e:
            logger.error(f"Error generating submission summary: {str(e)}")
            return "Submission completed"
    
    def _broadcast_rating_update(self, session_code, team, mission_type, rating_obj):
        """Broadcast rating update to all connected teachers"""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"design_thinking_{session_code}",
                    {
                        'type': 'rating_updated',
                        'team_id': team.id,
                        'team_name': team.team_name,
                        'mission_type': mission_type,
                        'rating': rating_obj.rating,
                        'rating_stars': rating_obj.rating_stars,
                        'feedback': rating_obj.feedback,
                        'average_rating': team.average_rating,
                        'timestamp': timezone.now().isoformat()
                    }
                )
        except Exception as e:
            logger.error(f"Error broadcasting rating update: {str(e)}")


@method_decorator(login_required, name='dispatch')
class TeamSubmissionDetailView(View):
    """Get detailed submission data for rating"""
    
    def get(self, request, session_code, team_id, mission_type):
        try:
            session = get_object_or_404(DesignThinkingSession, session_code=session_code)
            team = get_object_or_404(DesignTeam, id=team_id, session=session)
            mission = get_object_or_404(DesignMission, 
                                      game=session.design_game, 
                                      mission_type=mission_type)
            
            # Get all submissions for this mission
            submissions = team.phase_inputs.filter(
                mission=mission
            ).order_by('-submitted_at')
            
            submissions_data = []
            for submission in submissions:
                submissions_data.append({
                    'id': submission.id,
                    'input_data': submission.input_data,
                    'submitted_at': submission.submitted_at.isoformat(),
                    'student_name': getattr(submission, 'student_name', 'Unknown')
                })
            
            # Get existing rating
            existing_rating = team.get_phase_rating(mission_type)
            rating_data = None
            if existing_rating:
                rating_data = {
                    'id': existing_rating.id,
                    'rating': existing_rating.rating,
                    'rating_stars': existing_rating.rating_stars,
                    'feedback': existing_rating.feedback,
                    'quick_notes': existing_rating.quick_notes,
                    'rated_at': existing_rating.rated_at.isoformat()
                }
            
            return JsonResponse({
                'success': True,
                'team': {
                    'id': team.id,
                    'name': team.team_name,
                    'emoji': team.team_emoji,
                    'members': team.team_members
                },
                'mission': {
                    'type': mission.mission_type,
                    'title': mission.title,
                    'description': mission.description
                },
                'submissions': submissions_data,
                'existing_rating': rating_data,
                'submission_count': len(submissions_data)
            })
            
        except Exception as e:
            logger.error(f"Error fetching team submission details: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Failed to fetch submission details'
            }, status=500)


@method_decorator(login_required, name='dispatch')
class SessionRatingsExportView(View):
    """Export ratings to CSV/PDF"""
    
    def get(self, request, session_code):
        import csv
        from django.http import HttpResponse
        
        try:
            session = get_object_or_404(DesignThinkingSession, session_code=session_code)
            format_type = request.GET.get('format', 'csv')
            
            if format_type == 'csv':
                return self._export_csv(session)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Only CSV export supported currently'
                }, status=400)
                
        except Exception as e:
            logger.error(f"Error exporting ratings: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Failed to export ratings'
            }, status=500)
    
    def _export_csv(self, session):
        """Export ratings as CSV"""
        from django.http import HttpResponse
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="ratings_{session.session_code}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Team Name', 'Phase', 'Rating', 'Feedback', 'Quick Notes', 
            'Submission Summary', 'Rated At', 'Teacher'
        ])
        
        # Write data
        ratings = TeamPhaseRating.objects.filter(
            session=session
        ).select_related('team', 'mission', 'teacher').order_by('team__team_name', 'mission__order')
        
        for rating in ratings:
            writer.writerow([
                rating.team.team_name,
                rating.mission.get_mission_type_display(),
                f"{rating.rating} Stars",
                rating.feedback,
                rating.quick_notes,
                rating.submission_summary,
                rating.rated_at.strftime('%Y-%m-%d %H:%M'),
                rating.teacher.get_full_name() or rating.teacher.username
            ])
        
        return response


@method_decorator(login_required, name='dispatch')
class PhaseStatisticsView(View):
    """Get phase completion and rating statistics"""
    
    def get(self, request, session_code):
        try:
            session = get_object_or_404(DesignThinkingSession, session_code=session_code)
            
            # Get all teams and missions
            teams = session.design_teams.all()
            missions = session.design_game.missions.filter(is_active=True).order_by('order')
            
            # Calculate statistics
            stats = {
                'session_overview': {
                    'total_teams': teams.count(),
                    'total_phases': missions.count(),
                    'completion_rate': 0,
                    'average_rating': 0
                },
                'phase_stats': [],
                'team_stats': []
            }
            
            # Phase statistics
            for mission in missions:
                ratings = TeamPhaseRating.objects.filter(session=session, mission=mission)
                submissions = SimplifiedPhaseInput.objects.filter(session=session, mission=mission).values('team').distinct()
                
                phase_stat = {
                    'mission_type': mission.mission_type,
                    'mission_title': mission.title,
                    'teams_submitted': submissions.count(),
                    'teams_rated': ratings.count(),
                    'average_rating': ratings.aggregate(avg=Avg('rating'))['avg'] or 0,
                    'completion_percentage': (submissions.count() / teams.count() * 100) if teams.count() > 0 else 0
                }
                stats['phase_stats'].append(phase_stat)
            
            # Team statistics
            for team in teams:
                team_ratings = team.phase_ratings.all()
                team_stat = {
                    'team_id': team.id,
                    'team_name': team.team_name,
                    'team_emoji': team.team_emoji,
                    'phases_completed': team_ratings.count(),
                    'average_rating': team.average_rating or 0,
                    'progress_percentage': team.get_progress_percentage()
                }
                stats['team_stats'].append(team_stat)
            
            # Overall session statistics
            all_ratings = TeamPhaseRating.objects.filter(session=session)
            if all_ratings.exists():
                stats['session_overview']['average_rating'] = round(
                    all_ratings.aggregate(avg=Avg('rating'))['avg'], 1
                )
            
            total_possible_submissions = teams.count() * missions.count()
            actual_submissions = SimplifiedPhaseInput.objects.filter(session=session).values('team', 'mission').distinct().count()
            if total_possible_submissions > 0:
                stats['session_overview']['completion_rate'] = round(
                    (actual_submissions / total_possible_submissions) * 100, 1
                )
            
            return JsonResponse({
                'success': True,
                'statistics': stats
            })
            
        except Exception as e:
            logger.error(f"Error generating statistics: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate statistics'
            }, status=500)