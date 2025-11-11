"""
Simplified Team Creation for Phase-Based Architecture
Clean, transaction-safe team joining that works with the new phase system
"""

from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
import logging

from .models import DesignThinkingSession, DesignTeam

logger = logging.getLogger(__name__)


class SimplifiedJoinView(TemplateView):
    """
    Simplified team creation that works with the new phase-based architecture
    Clean, transaction-safe, with proper error handling
    """
    template_name = 'group_learning/design_thinking/join_session.html'
    
    def _handle_error(self, request, message, field=None):
        """Handle error response consistently"""
        # Always return JSON for AJAX, redirect for regular requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': message,
                'field': field
            }, status=400)
        else:
            messages.error(request, message)
            return redirect('group_learning:create_simplified_session')
    
    def post(self, request):
        """Create team with full transaction safety"""
        
        # 1. Extract and validate input data
        session_code = request.POST.get('session_code', '').strip().upper()
        team_name = request.POST.get('team_name', '').strip()
        team_emoji = request.POST.get('team_emoji', '💡').strip()
        
        # Basic validation
        if not session_code:
            return self._handle_error(request, 'Session code is required', 'session_code')
        
        if not team_name:
            return self._handle_error(request, 'Team name is required', 'team_name')
        
        if len(team_name) > 50:
            return self._handle_error(request, 'Team name must be 50 characters or less', 'team_name')
            
        # Process team members (optional for simplified mode)
        team_members = []
        team_members_json = request.POST.get('team_members', '[]')
        try:
            import json
            parsed_members = json.loads(team_members_json)
            if isinstance(parsed_members, list):
                team_members = [str(member).strip() for member in parsed_members if str(member).strip()]
        except (json.JSONDecodeError, ValueError):
            # If team members can't be parsed, just use empty list - not critical
            team_members = []
        
        # 2. Database operations with full transaction safety
        try:
            with transaction.atomic():
                # Find session
                session = get_object_or_404(
                    DesignThinkingSession.objects.select_for_update(),
                    session_code=session_code
                )
                
                # Quick session validation
                if session.status in ['completed', 'abandoned']:
                    return self._handle_error(request, 'This session is no longer active', 'session_code')
                
                # Check team limit (reasonable limit for simplified mode)
                current_team_count = session.design_teams.count()
                if current_team_count >= 50:  # Reduced from 100 for simplicity
                    return self._handle_error(request, 'Session is full (maximum 50 teams)', 'session_code')
                
                # Create team - this is where the unique constraint could fail
                try:
                    team = DesignTeam.objects.create(
                        session=session,
                        team_name=team_name,
                        team_emoji=team_emoji,
                        team_members=team_members,
                        team_color='#3B82F6'  # Default blue
                    )
                    logger.info(f"Team created successfully: {team_name} in session {session_code}")
                    
                except Exception as create_error:
                    # Handle specific constraint violations
                    error_msg = str(create_error).lower()
                    if 'unique' in error_msg and 'team_name' in error_msg:
                        return self._handle_error(
                            request,
                            f'Team name "{team_name}" is already taken in this session. Please choose a different name.',
                            'team_name'
                        )
                    else:
                        logger.error(f"Unexpected team creation error: {create_error}")
                        return self._handle_error(request, 'Failed to create team. Please try again.')
                
                # 3. Set session data for phase navigation
                request.session[f'team_id_{session_code}'] = team.id
                request.session['current_session_code'] = session_code
                
                # 4. Success - redirect to phase entry point
                logger.info(f"Team {team_name} successfully joined session {session_code}")
                
                # For AJAX requests, return success JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect_url': f'/learn/simplified/{session_code}/student/',
                        'message': f'Welcome, Team {team_name} {team_emoji}!'
                    })
                
                # For regular requests, show success and redirect
                messages.success(request, f'Welcome, Team {team_name} {team_emoji}!')
                return redirect('group_learning:student_entry', session_code=session_code)
                
        except DesignThinkingSession.DoesNotExist:
            return self._handle_error(request, f'Session {session_code} not found', 'session_code')
            
        except Exception as e:
            # Catch-all for unexpected errors - transaction will auto-rollback
            logger.error(f"Unexpected error during team creation: {e}", exc_info=True)
            return self._handle_error(request, 'An error occurred. Please try again.')


# For backward compatibility, create an alias
DesignThinkingJoinView = SimplifiedJoinView