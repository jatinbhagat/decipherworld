from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, TemplateView, View
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from django.forms import ModelForm, CharField, ChoiceField
from django.core.exceptions import ValidationError
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.conf import settings
import random
import string
import json
import logging

from .models import (
    Game, GameSession, Role, Scenario, Action, Outcome, 
    PlayerAction, ReflectionResponse, LearningObjective,
    ConstitutionQuestion, ConstitutionOption, ConstitutionTeam, 
    CountryState, ConstitutionAnswer,
    DesignThinkingGame, DesignMission, DesignThinkingSession,
    DesignTeam, TeamProgress, TeamSubmission, MentorNudge
)
from .cache_utils import ConstitutionCache, cache_view_response
from .services import DesignThinkingService, SubmissionService, MissionAdvancementError


class GameListView(ListView):
    """Display available games for group learning"""
    model = Game
    template_name = 'group_learning/game_list.html'
    context_object_name = 'games'
    queryset = Game.objects.filter(is_active=True).order_by('title')


class GameDetailView(DetailView):
    """Show detailed information about a game"""
    model = Game
    template_name = 'group_learning/game_detail.html'
    context_object_name = 'game'
    queryset = Game.objects.filter(is_active=True).prefetch_related(
        'learning_objectives',
        'scenarios__learning_objectives',
        'scenarios__required_roles'
    )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.get_object()
        context['scenarios'] = game.scenarios.filter(is_active=True).order_by('order')
        context['roles'] = Role.objects.filter(is_active=True, scenario__game=game).distinct()
        return context


class SessionForm(ModelForm):
    """Form for creating a new game session"""
    facilitator_name = CharField(max_length=100, required=False, 
                               help_text="Optional: Enter your name as the session facilitator")
    
    class Meta:
        model = GameSession
        fields = ['allow_spectators', 'auto_assign_roles']
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Generate unique session code
        instance.session_code = self._generate_session_code()
        if commit:
            instance.save()
        return instance
    
    def _generate_session_code(self):
        """Generate a unique 6-character session code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not GameSession.objects.filter(session_code=code).exists():
                return code


class CreateSessionView(CreateView):
    """Create a new game session"""
    model = GameSession
    form_class = SessionForm
    template_name = 'group_learning/create_session.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game_id = self.kwargs['game_id']
        context['game'] = get_object_or_404(Game, id=game_id, is_active=True)
        return context
    
    def form_valid(self, form):
        game_id = self.kwargs['game_id']
        game = get_object_or_404(Game, id=game_id, is_active=True)
        
        form.instance.game = game
        form.instance.status = 'waiting'
        
        # Set facilitator name if provided
        facilitator_name = form.cleaned_data.get('facilitator_name')
        if facilitator_name:
            form.instance.session_data = {'facilitator_name': facilitator_name}
        
        messages.success(self.request, f'Session created successfully! Session code: {form.instance.session_code}')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('group_learning:session_detail', kwargs={'session_code': self.object.session_code})


class JoinSessionForm(ModelForm):
    """Form for joining a game session"""
    player_name = CharField(max_length=100, help_text="Enter your name")
    preferred_role = ChoiceField(required=False, help_text="Optional: Choose preferred role")
    
    class Meta:
        model = GameSession
        fields = []
    
    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        
        if self.session:
            # Add role choices based on game - handle case where session.game is None
            if self.session.game:
                roles = Role.objects.filter(
                    scenario__game=self.session.game,
                    is_active=True
                ).distinct().values_list('id', 'name')
            else:
                # If no game assigned, show all active roles
                roles = Role.objects.filter(is_active=True).values_list('id', 'name')
            self.fields['preferred_role'].choices = [('', 'No preference')] + list(roles)


class SessionDetailView(DetailView):
    """Display session information and allow players to join"""
    model = GameSession
    template_name = 'group_learning/session_detail.html'
    context_object_name = 'session'
    slug_field = 'session_code'
    slug_url_kwarg = 'session_code'
    queryset = GameSession.objects.select_related('game', 'current_scenario').prefetch_related(
        'player_actions__role',
        'game__scenarios__required_roles'
    )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.get_object()
        
        # Get unique players in session
        players = session.player_actions.values('player_name', 'player_session_id').distinct()
        context['players'] = players
        context['player_count'] = len(players)
        
        # Get available roles - handle case where session.game is None
        if session.game:
            context['available_roles'] = Role.objects.filter(
                scenario__game=session.game,
                is_active=True
            ).distinct()
        else:
            # If no game assigned, show all active roles
            context['available_roles'] = Role.objects.filter(is_active=True)
        
        context['join_form'] = JoinSessionForm(session=session)
        return context


class JoinSessionView(View):
    """Handle player joining a session"""
    
    def post(self, request, session_code):
        session = get_object_or_404(GameSession, session_code=session_code)
        
        # Check if session is still open for joining
        if session.status not in ['waiting', 'in_progress']:
            messages.error(request, 'This session is no longer accepting players.')
            return redirect('group_learning:session_detail', session_code=session_code)
        
        form = JoinSessionForm(request.POST, session=session)
        if form.is_valid():
            player_name = form.cleaned_data['player_name']
            preferred_role = form.cleaned_data.get('preferred_role')
            
            # Generate unique player session ID
            player_session_id = self._generate_player_id(session)
            
            # Store player info in session data
            session_data = session.session_data or {}
            players = session_data.get('players', {})
            players[player_session_id] = {
                'name': player_name,
                'preferred_role': preferred_role,
                'joined_at': timezone.now().isoformat(),
            }
            session_data['players'] = players
            session.session_data = session_data
            session.save()
            
            # Set player info in session
            request.session['player_name'] = player_name
            request.session['player_session_id'] = player_session_id
            request.session['current_game_session'] = session_code
            
            messages.success(request, f'Successfully joined session as {player_name}!')
            return redirect('group_learning:gameplay', session_code=session_code)
        else:
            messages.error(request, 'Please fix the errors below.')
            return redirect('group_learning:session_detail', session_code=session_code)
    
    def _generate_player_id(self, session):
        """Generate unique player ID for this session"""
        session_data = session.session_data or {}
        players = session_data.get('players', {})
        
        while True:
            player_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            if player_id not in players:
                return player_id


class GameplayView(TemplateView):
    """Main gameplay interface"""
    template_name = 'group_learning/gameplay.html'
    
    def get(self, request, *args, **kwargs):
        session_code = kwargs['session_code']
        
        # Check if player is in session
        player_session_id = request.session.get('player_session_id')
        if not player_session_id:
            messages.error(request, 'You must join the session first.')
            return redirect('group_learning:session_detail', session_code=session_code)
            
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs['session_code']
        session = get_object_or_404(
            GameSession.objects.select_related('game', 'current_scenario').prefetch_related(
                'game__scenarios__actions__role',
                'player_actions__role',
                'player_actions__action'
            ),
            session_code=session_code
        )
        
        # Player session ID is guaranteed to exist from get method
        player_session_id = self.request.session.get('player_session_id')
        
        context['session'] = session
        context['player_name'] = self.request.session.get('player_name')
        context['player_session_id'] = player_session_id
        
        # Get current scenario
        current_scenario = session.current_scenario
        if not current_scenario:
            # Start with first scenario
            current_scenario = session.game.scenarios.filter(is_active=True).order_by('order').first()
            if current_scenario:
                session.current_scenario = current_scenario
                session.status = 'in_progress'
                session.started_at = timezone.now()
                session.save()
        
        context['current_scenario'] = current_scenario
        
        # Get player's assigned role
        player_role = self._get_player_role(session, player_session_id)
        context['player_role'] = player_role
        
        # Get available actions for player's role
        if player_role and current_scenario:
            available_actions = current_scenario.actions.filter(
                role=player_role,
                is_active=True
            ).select_related('role')
            context['available_actions'] = available_actions
        
        # Get previous actions by this player
        context['player_actions'] = PlayerAction.objects.filter(
            session=session,
            player_session_id=player_session_id
        ).select_related('role', 'action', 'scenario').order_by('-decision_time')
        
        return context
    
    def _get_player_role(self, session, player_session_id):
        """Get or assign role to player"""
        # Check if player already has a role assigned
        existing_action = PlayerAction.objects.filter(
            session=session,
            player_session_id=player_session_id
        ).first()
        
        if existing_action:
            return existing_action.role
        
        # Auto-assign role if enabled
        if session.auto_assign_roles:
            return self._auto_assign_role(session, player_session_id)
        
        return None
    
    def _auto_assign_role(self, session, player_session_id):
        """Automatically assign a role to the player"""
        # Get session data to check preferred role
        session_data = session.session_data or {}
        players = session_data.get('players', {})
        player_info = players.get(player_session_id, {})
        preferred_role_id = player_info.get('preferred_role')
        
        # Get available roles for current scenario
        if session.current_scenario:
            available_roles = session.current_scenario.required_roles.filter(is_active=True)
        else:
            available_roles = Role.objects.filter(
                scenario__game=session.game,
                is_active=True
            ).distinct()
        
        # Check which roles are already taken
        assigned_roles = PlayerAction.objects.filter(
            session=session
        ).values_list('role', flat=True).distinct()
        
        unassigned_roles = available_roles.exclude(id__in=assigned_roles)
        
        # Try to assign preferred role first
        if preferred_role_id:
            try:
                preferred_role = unassigned_roles.get(id=preferred_role_id)
                return preferred_role
            except Role.DoesNotExist:
                pass
        
        # Assign first available role
        return unassigned_roles.first()


class PlayerActionView(View):
    """Handle player action submission"""
    
    def post(self, request, session_code):
        session = get_object_or_404(GameSession, session_code=session_code)
        
        # Validate player is in session
        player_session_id = request.session.get('player_session_id')
        if not player_session_id:
            return JsonResponse({'error': 'Not in session'}, status=400)
        
        action_id = request.POST.get('action_id')
        reasoning = request.POST.get('reasoning', '')
        
        if not action_id:
            return JsonResponse({'error': 'No action specified'}, status=400)
        
        action = get_object_or_404(Action, id=action_id)
        
        # Get or assign player role
        player_role = self._get_or_assign_role(session, player_session_id, action.role)
        
        # Create player action record
        player_action = PlayerAction.objects.create(
            session=session,
            scenario=session.current_scenario,
            role=player_role,
            action=action,
            player_name=request.session.get('player_name'),
            player_session_id=player_session_id,
            reasoning=reasoning,
            round_number=1,  # TODO: Implement round tracking
            is_final_decision=True
        )
        
        messages.success(request, f'Action "{action.title}" submitted successfully!')
        return JsonResponse({'success': True, 'action_id': player_action.id})
    
    def _get_or_assign_role(self, session, player_session_id, required_role):
        """Get player's existing role or assign the required role"""
        existing_action = PlayerAction.objects.filter(
            session=session,
            player_session_id=player_session_id
        ).first()
        
        if existing_action:
            return existing_action.role
        
        return required_role


class SessionResultsView(DetailView):
    """Show session results and outcomes"""
    model = GameSession
    template_name = 'group_learning/session_results.html'
    context_object_name = 'session'
    slug_field = 'session_code'
    slug_url_kwarg = 'session_code'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.get_object()
        
        # Get all player actions
        player_actions = session.player_actions.all().order_by('role', 'decision_time')
        context['player_actions'] = player_actions
        
        # Calculate outcome based on actions taken
        outcome = self._calculate_outcome(session, player_actions)
        context['outcome'] = outcome
        
        # Get learning objectives covered
        if session.current_scenario:
            context['learning_objectives'] = session.current_scenario.learning_objectives.all()
        
        return context
    
    def _calculate_outcome(self, session, player_actions):
        """Calculate the outcome based on actions taken"""
        if not session.current_scenario:
            return None
        
        # Get all possible outcomes for the scenario
        outcomes = session.current_scenario.outcomes.filter(is_active=True)
        
        # Simple outcome calculation - match based on required actions
        actions_taken = set(player_actions.values_list('action', flat=True))
        
        best_outcome = None
        best_match_score = 0
        
        for outcome in outcomes:
            required_actions = set(outcome.required_actions.all().values_list('id', flat=True))
            
            if not required_actions:  # No requirements - fallback outcome
                if not best_outcome:
                    best_outcome = outcome
                continue
            
            match_score = len(actions_taken.intersection(required_actions)) / len(required_actions)
            
            if match_score > best_match_score:
                best_match_score = match_score
                best_outcome = outcome
        
        return best_outcome


class ReflectionView(TemplateView):
    """Post-game reflection and learning assessment"""
    template_name = 'group_learning/reflection.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs['session_code']
        session = get_object_or_404(GameSession, session_code=session_code)
        
        context['session'] = session
        context['player_name'] = self.request.session.get('player_name')
        
        # Get learning objectives for reflection
        if session.current_scenario:
            context['learning_objectives'] = session.current_scenario.learning_objectives.all()
        
        return context
    
    def post(self, request, session_code):
        """Handle reflection response submission"""
        session = get_object_or_404(GameSession, session_code=session_code)
        
        player_session_id = request.session.get('player_session_id')
        if not player_session_id:
            messages.error(request, 'Session expired.')
            return redirect('group_learning:session_detail', session_code=session_code)
        
        # Get player's role from their actions
        player_action = session.player_actions.filter(
            player_session_id=player_session_id
        ).first()
        
        if not player_action:
            messages.error(request, 'You must participate in the game before reflecting.')
            return redirect('group_learning:gameplay', session_code=session_code)
        
        role_played = player_action.role
        
        # Save reflection responses
        for key, value in request.POST.items():
            if key.startswith('reflection_'):
                obj_id = key.replace('reflection_', '')
                try:
                    learning_objective = LearningObjective.objects.get(id=obj_id)
                    confidence_level = request.POST.get(f'confidence_{obj_id}', 3)
                    engagement_level = request.POST.get(f'engagement_{obj_id}', 3)
                    
                    ReflectionResponse.objects.create(
                        session=session,
                        scenario=session.current_scenario,
                        learning_objective=learning_objective,
                        player_name=request.session.get('player_name'),
                        player_session_id=player_session_id,
                        role_played=role_played,
                        question=f"Reflection on {learning_objective.title}",
                        response=value,
                        confidence_level=int(confidence_level),
                        engagement_level=int(engagement_level)
                    )
                except (LearningObjective.DoesNotExist, ValueError):
                    continue
        
        messages.success(request, 'Thank you for your reflection!')
        return redirect('group_learning:session_results', session_code=session_code)


# API Views for real-time updates

class SessionStatusAPI(View):
    """API endpoint for session status updates"""
    
    def get(self, request, session_code):
        session = get_object_or_404(
            GameSession.objects.select_related('game', 'current_scenario'),
            session_code=session_code
        )
        
        # Get enhanced session status
        active_players = session.get_active_players()
        role_coverage = session.get_role_coverage()
        
        # Serialize active players properly
        active_players_data = []
        if active_players:
            # Convert QuerySet to list first
            players_list = list(active_players)
            for player in players_list:
                active_players_data.append({
                    'id': player.get('player_session_id', ''),
                    'name': player.get('player_name', ''),
                    'role': player.get('role_name', None),
                    'last_activity': player.get('latest_action').isoformat() if player.get('latest_action') else None
                })
        
        # Serialize role coverage properly  
        role_coverage_data = {}
        if role_coverage:
            # Convert QuerySet to list for JSON serialization
            filled_roles = role_coverage.get('filled', [])
            if hasattr(filled_roles, 'all'):  # It's a QuerySet
                filled_roles = list(filled_roles)
            
            role_coverage_data = {
                'filled': filled_roles,
                'required': role_coverage.get('required', []),
                'missing': role_coverage.get('missing', [])
            }
        
        return JsonResponse({
            'status': session.status,
            'player_count': session.get_player_count(),
            'current_scenario': session.current_scenario.title if session.current_scenario else None,
            'game_title': session.game.title,
            'is_ready_to_start': session.is_ready_to_start(),
            'active_players': active_players_data,
            'role_coverage': role_coverage_data,
            'min_players': session.game.min_players,
            'max_players': session.game.max_players,
            'last_activity': timezone.now().isoformat()  # For polling efficiency
        })


class SessionDashboardView(TemplateView):
    """Collaborative session dashboard for teachers and facilitators"""
    template_name = 'group_learning/session_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs['session_code']
        session = get_object_or_404(
            GameSession.objects.select_related('game', 'current_scenario'),
            session_code=session_code
        )
        
        context['session'] = session
        context['player_count'] = session.get_player_count()
        context['active_players'] = session.get_active_players()
        
        return context


class SessionActionsAPI(View):
    """API endpoint for getting recent actions in session"""
    
    def get(self, request, session_code):
        session = get_object_or_404(GameSession, session_code=session_code)
        
        # Get recent actions
        recent_actions = session.player_actions.select_related('role', 'action').order_by('-decision_time')[:10]
        
        actions_data = []
        for action in recent_actions:
            actions_data.append({
                'player_name': action.player_name,
                'role': action.role.short_name,
                'action_title': action.action.title,
                'decision_time': action.decision_time.strftime('%H:%M:%S'),
                'reasoning': action.reasoning[:100] + '...' if len(action.reasoning) > 100 else action.reasoning
            })
        
        return JsonResponse({'actions': actions_data})


# Constitution Challenge Game Views

class ConstitutionGameView(TemplateView):
    """Main gameplay view for Constitution Challenge"""
    template_name = 'group_learning/constitution_gameplay.html'
    
    def get(self, request, *args, **kwargs):
        session_code = kwargs.get('session_code')
        team_id = request.GET.get('team_id') or request.session.get('team_id')
        
        # Get session and validate
        session = get_object_or_404(GameSession, session_code=session_code)
        if session.game.game_type != 'constitution_challenge':
            messages.error(request, 'This session is not a Constitution Challenge game.')
            return redirect('group_learning:session_detail', session_code=session_code)
        
        # Get or create team
        team = None
        if team_id:
            try:
                team = ConstitutionTeam.objects.get(id=team_id, session=session)
                # Store team in session for future requests
                request.session['team_id'] = team.id
            except ConstitutionTeam.DoesNotExist:
                pass
        
        # If no team found, redirect to team creation page
        if not team:
            return redirect('group_learning:constitution_join', session_code=session_code)
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs.get('session_code')
        team_id = self.request.GET.get('team_id') or self.request.session.get('team_id')
        
        # Get session and team (we know they exist from get method)
        session = get_object_or_404(GameSession, session_code=session_code)
        team = ConstitutionTeam.objects.get(id=team_id, session=session)
        
        context.update({
            'session': session,
            'team': team,
            'game': session.game,
        })
        
        if team:
            # Get current question
            current_question = team.current_question
            if not current_question:
                # Get first unanswered question
                answered_question_ids = team.answers.values_list('question_id', flat=True)
                current_question = session.game.constitution_questions.filter(
                    is_active=True
                ).exclude(id__in=answered_question_ids).order_by('order').first()
                
                if current_question:
                    team.current_question = current_question
                    team.save()
            
            # Get country state
            country_state, created = CountryState.objects.get_or_create(team=team)
            if created:
                country_state.update_from_score(team.total_score)
            
            # Prepare governance scores for template
            governance_scores = {
                'democracy': country_state.democracy_score,
                'fairness': country_state.fairness_score, 
                'freedom': country_state.freedom_score,
                'stability': country_state.stability_score,
            }
            
            context.update({
                'current_question': current_question,
                'country_state': country_state,
                'governance_scores': governance_scores,
                'governance_level': team.get_governance_level(),
                'team_rank': team.get_rank_in_session(),
                'progress_percentage': (team.questions_completed / 
                                      session.game.constitution_questions.count() * 100) 
                                     if session.game.constitution_questions.count() > 0 else 0,
            })
        
        return context


class ConstitutionTeamCreateView(View):
    """Handle team creation for Constitution Challenge"""
    
    def post(self, request, session_code):
        session = get_object_or_404(GameSession, session_code=session_code)
        
        if session.game.game_type != 'constitution_challenge':
            return JsonResponse({'error': 'Not a Constitution Challenge game'}, status=400)
        
        # Get form data
        team_name = request.POST.get('team_name', '').strip()
        team_avatar = request.POST.get('team_avatar', '🏛️')
        country_color = request.POST.get('country_color', '#3B82F6')
        flag_emoji = request.POST.get('flag_emoji', '🏴')
        
        if not team_name:
            return JsonResponse({'error': 'Team name is required'}, status=400)
        
        # Check if team name already exists in this session
        if ConstitutionTeam.objects.filter(session=session, team_name=team_name).exists():
            return JsonResponse({'error': 'Team name already exists'}, status=400)
        
        # Create team
        team = ConstitutionTeam.objects.create(
            session=session,
            team_name=team_name,
            team_avatar=team_avatar,
            country_color=country_color,
            flag_emoji=flag_emoji
        )
        
        # Create initial country state
        CountryState.objects.create(team=team)
        
        # Store team in session
        request.session['team_id'] = team.id
        
        return JsonResponse({
            'success': True,
            'team_id': team.id,
            'redirect_url': reverse('group_learning:constitution_game', 
                                  kwargs={'session_code': session_code}) + f'?team_id={team.id}'
        })


class ConstitutionQuestionAPI(View):
    """API endpoint for getting current question data"""
    
    def get(self, request, session_code):
        # Optimize query with select_related to avoid N+1 queries
        session = get_object_or_404(
            GameSession.objects.select_related('game'),
            session_code=session_code
        )
        team_id = request.GET.get('team_id') or request.session.get('team_id')
        
        if not team_id:
            return JsonResponse({'error': 'Team ID required'}, status=400)
        
        try:
            # Optimize team query with select_related and prefetch_related
            team = ConstitutionTeam.objects.select_related(
                'session__game',
                'country_state'
            ).prefetch_related(
                'answers__question',
                'answers__chosen_option'
            ).get(id=team_id, session=session)
        except ConstitutionTeam.DoesNotExist:
            return JsonResponse({'error': 'Team not found'}, status=404)
        
        current_question = team.current_question
        if not current_question:
            # Check if game is complete
            total_questions = session.game.constitution_questions.count()
            if team.questions_completed >= total_questions:
                return JsonResponse({
                    'game_completed': True,
                    'final_score': team.total_score,
                    'governance_level': team.get_governance_level(),
                    'rank': team.get_rank_in_session()
                })
            
            return JsonResponse({'error': 'No current question'}, status=404)
        
        # Get options for current question
        options = []
        for option in current_question.options.filter(is_active=True).order_by('option_letter'):
            options.append({
                'id': option.id,
                'letter': option.option_letter,
                'text': option.option_text,
                'color_class': option.color_class,
            })
        
        # Get country state with caching
        cached_visual_state = ConstitutionCache.get_team_visual_state(team.id)
        if not cached_visual_state:
            country_state = CountryState.objects.get(team=team)
            cached_visual_state = {
                'level': country_state.current_city_level,
                'level_display': country_state.get_current_city_level_display(),
                'democracy_score': country_state.democracy_score,
                'fairness_score': country_state.fairness_score,
                'freedom_score': country_state.freedom_score,
                'stability_score': country_state.stability_score,
                'unlocked_features': getattr(country_state, 'unlocked_features', []),
                'visual_elements': country_state.visual_elements,
            }
        
        return JsonResponse({
            'question': {
                'id': current_question.id,
                'text': current_question.question_text,
                'category': current_question.get_category_display(),
                'scenario_context': current_question.scenario_context,
                'time_limit': current_question.time_limit,
                'order': current_question.order,
            },
            'options': options,
            'team': {
                'id': team.id,
                'name': team.team_name,
                'score': team.total_score,
                'avatar': team.team_avatar,
                'color': team.country_color,
                'flag': team.flag_emoji,
                'questions_completed': team.questions_completed,
            },
            'country_state': cached_visual_state,
            'progress': {
                'current': team.questions_completed + 1,
                'total': session.game.constitution_questions.count(),
                'percentage': ((team.questions_completed + 1) / 
                             session.game.constitution_questions.count() * 100) 
                            if session.game.constitution_questions.count() > 0 else 0,
            },
            'leaderboard': ConstitutionCache.get_session_leaderboard(session.id)[:5]  # Top 5 for API
        })


class ConstitutionAnswerAPI(View):
    """API endpoint for submitting answers"""
    
    def post(self, request, session_code):
        # Optimize session query
        session = get_object_or_404(
            GameSession.objects.select_related('game'),
            session_code=session_code
        )
        team_id = request.POST.get('team_id') or request.session.get('team_id')
        option_id = request.POST.get('option_id')
        
        if not team_id or not option_id:
            return JsonResponse({'error': 'Team ID and option ID required'}, status=400)
        
        try:
            # Optimize queries with select_related and prefetch_related
            team = ConstitutionTeam.objects.select_related(
                'session__game',
                'country_state'
            ).prefetch_related(
                'answers__question'
            ).get(id=team_id, session=session)
            
            option = ConstitutionOption.objects.select_related(
                'question__game'
            ).get(id=option_id)
        except (ConstitutionTeam.DoesNotExist, ConstitutionOption.DoesNotExist):
            return JsonResponse({'error': 'Team or option not found'}, status=404)
        
        question = option.question
        
        # Check if already answered
        if ConstitutionAnswer.objects.filter(team=team, question=question).exists():
            return JsonResponse({'error': 'Question already answered'}, status=400)
        
        # Calculate time taken (mock for now - would be tracked in frontend)
        time_taken = 30  # Default time
        
        # Record answer
        score_before = team.total_score
        points_earned = option.score_value
        score_after = score_before + points_earned
        
        answer = ConstitutionAnswer.objects.create(
            team=team,
            question=question,
            chosen_option=option,
            time_taken=time_taken,
            points_earned=points_earned,
            score_before=score_before,
            score_after=score_after,
        )
        
        # Update team score and progress
        team.total_score = score_after
        team.questions_completed += 1
        
        # Move to next question
        next_question = session.game.constitution_questions.filter(
            is_active=True,
            order__gt=question.order
        ).order_by('order').first()
        
        team.current_question = next_question
        
        # Check if game is complete
        if not next_question:
            team.is_completed = True
            team.completion_time = timezone.now()
        
        team.save()
        
        # Update country state
        country_state = CountryState.objects.get(team=team)
        country_state.update_from_score(team.total_score)
        
        # Get learning module content for response (NEW ENHANCED SYSTEM)
        learning_content = self.get_learning_module_for_answer(
            question, option, team.total_score
        )
        
        return JsonResponse({
            'success': True,
            'feedback': {
                'message': option.feedback_message,
                'points_earned': points_earned,
                'governance_principle': option.governance_principle,
            },
            'team_update': {
                'new_score': team.total_score,
                'questions_completed': team.questions_completed,
                'governance_level': team.get_governance_level(),
                'rank': team.get_rank_in_session(),
            },
            'country_state': {
                'level': country_state.current_city_level,
                'level_display': country_state.get_current_city_level_display(),
                'democracy_score': country_state.democracy_score,
                'fairness_score': country_state.fairness_score,
                'freedom_score': country_state.freedom_score,
                'stability_score': country_state.stability_score,
                'unlocked_features': country_state.unlocked_features,
                'new_features': [f for f in country_state.unlocked_features 
                               if f not in (country_state.unlocked_features or [])],
                'visual_elements': country_state.visual_elements,
            },
            'learning_module': learning_content,
            'game_completed': team.is_completed,
            'next_question': next_question is not None,
        })

    def get_learning_module_for_answer(self, question, option, team_score):
        """
        Get appropriate enhanced learning module based on question, option, and team performance
        """
        from .models import GameLearningModule
        
        # Try to find a GameLearningModule for this specific context
        learning_module = None
        
        # Priority 1: Option-based trigger (most specific)
        if not learning_module:
            learning_module = GameLearningModule.objects.filter(
                game_type='constitution_challenge',
                trigger_condition='option_based',
                trigger_option=option,
                is_enabled=True
            ).first()
        
        # Priority 2: Question-based trigger
        if not learning_module:
            learning_module = GameLearningModule.objects.filter(
                game_type='constitution_challenge',
                trigger_condition='question_based',
                trigger_question=question,
                is_enabled=True
            ).first()
        
        # Priority 3: Topic-based trigger
        if not learning_module:
            learning_module = GameLearningModule.objects.filter(
                game_type='constitution_challenge',
                trigger_condition='topic_based',
                trigger_topic=question.category,
                is_enabled=True
            ).first()
        
        # Priority 4: Score-based trigger
        if not learning_module:
            learning_module = GameLearningModule.objects.filter(
                game_type='constitution_challenge',
                trigger_condition='score_based',
                min_score__lte=team_score,
                max_score__gte=team_score,
                is_enabled=True
            ).first()
        
        # Priority 5: Always show trigger (fallback)
        if not learning_module:
            learning_module = GameLearningModule.objects.filter(
                game_type='constitution_challenge',
                trigger_condition='always',
                is_enabled=True
            ).first()
        
        # Convert GameLearningModule to dictionary format expected by frontend
        if learning_module:
            # Increment view count
            learning_module.view_count = (learning_module.view_count or 0) + 1
            learning_module.save(update_fields=['view_count'])
            
            print(f"🚀 BACKEND: Found learning module '{learning_module.title}'")
            print(f"   Has governance_impact: {bool(learning_module.governance_impact)}")
            print(f"   Has constitution_principle: {bool(learning_module.constitution_principle)}")
            print(f"🎯 CHOICE: User selected option '{option.option_letter}': {option.option_text[:50]}...")
            
            # **DYNAMIC CONTENT**: Prioritize choice-specific impact over generic module content
            choice_governance_impact = option.governance_impact or learning_module.governance_impact or ''
            choice_score_reasoning = option.score_reasoning or learning_module.score_reasoning or ''
            choice_country_changes = option.country_state_changes or learning_module.country_state_changes or ''
            choice_societal_impact = option.societal_impact or learning_module.societal_impact or ''
            
            print(f"   Using choice-specific content: {bool(option.governance_impact or option.score_reasoning)}")
            
            return {
                'title': learning_module.title,
                'principle_explanation': learning_module.principle_explanation or '',
                'key_takeaways': learning_module.key_takeaways or '',
                'historical_context': learning_module.historical_context or '',
                'real_world_example': learning_module.real_world_example or '',
                
                # Enhanced Part 1: Action Reasoning (DYNAMIC - Choice-Specific)
                'action_impact_title': f"Impact of Your Choice: Option {option.option_letter}",
                'governance_impact': choice_governance_impact,
                'score_reasoning': choice_score_reasoning,
                'country_state_changes': choice_country_changes,
                'societal_impact': choice_societal_impact,
                
                # Enhanced Part 2: Constitution Teaching (from learning module)
                'constitution_topic_title': learning_module.constitution_topic_title or 'Learn from the Indian Constitution',
                'constitution_principle': learning_module.constitution_principle or '',
                'constitution_explanation': learning_module.constitution_explanation or '',
                'constitution_article_reference': learning_module.constitution_article_reference or '',
                'historical_constitutional_context': learning_module.historical_constitutional_context or '',
                
                # Choice-specific metadata
                'selected_option': option.option_letter,
                'option_text': option.option_text,
                'score_change': option.score_value,
                'governance_principle': option.governance_principle or '',
                
                # Metadata
                'id': learning_module.id,
                'display_timing': learning_module.display_timing,
                'is_skippable': learning_module.is_skippable,
                'game_type': learning_module.get_game_type_display(),
            }
        
        # Fallback to legacy system if no GameLearningModule found
        if question.learning_module_title:
            return {
                'title': question.learning_module_title,
                'principle_explanation': question.learning_module_content or '',
                'key_takeaways': '',
                'historical_context': '',
                'real_world_example': '',
                
                # Empty enhanced fields for legacy content
                'action_impact_title': 'Impact of Your Decision',
                'governance_impact': '',
                'score_reasoning': '',
                'country_state_changes': '',
                'societal_impact': '',
                'constitution_topic_title': 'Learn from the Indian Constitution',
                'constitution_principle': '',
                'constitution_explanation': '',
                'constitution_article_reference': '',
                'historical_constitutional_context': '',
                
                'id': None,
                'display_timing': 'instant',
                'is_skippable': True,
                'game_type': 'Constitution Challenge',
            }
        
        return None


class ConstitutionLeaderboardAPI(View):
    """API endpoint for getting leaderboard data"""
    
    def get(self, request, session_code):
        session = get_object_or_404(GameSession, session_code=session_code)
        
        # Get all teams for this session, ordered by score
        teams = ConstitutionTeam.objects.filter(session=session).order_by(
            '-total_score', 'completion_time', 'created_at'
        )
        
        leaderboard = []
        for rank, team in enumerate(teams, 1):
            governance_level = team.get_governance_level()
            leaderboard.append({
                'rank': rank,
                'team_id': team.id,
                'team_name': team.team_name,
                'avatar': team.team_avatar,
                'flag': team.flag_emoji,
                'color': team.country_color,
                'score': team.total_score,
                'questions_completed': team.questions_completed,
                'governance_level': governance_level['description'],
                'governance_emoji': governance_level['emoji'],
                'is_completed': team.is_completed,
                'completion_time': team.completion_time.isoformat() if team.completion_time else None,
            })
        
        return JsonResponse({
            'leaderboard': leaderboard,
            'total_teams': len(leaderboard),
            'session_info': {
                'code': session.session_code,
                'game_title': session.game.title,
                'total_questions': session.game.constitution_questions.count(),
            }
        })


class ConstitutionQuickStartView(TemplateView):
    """Simplified Constitution Challenge start page - team name, optional session code, start playing"""
    template_name = 'group_learning/constitution_quick_start.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if this is for advanced or basic level
        level = kwargs.get('level', 'basic')
        
        # Get the appropriate Constitution Challenge game
        try:
            if level == 'advanced':
                # Get the Advanced Constitution Challenge
                game = Game.objects.filter(
                    game_type='constitution_challenge', 
                    is_active=True,
                    title__icontains='Advanced'
                ).first()
                context['game_level'] = 'Advanced'
                context['grade_range'] = 'Grades 9-12'
            else:
                # Get the basic Constitution Challenge (not the Advanced one)
                game = Game.objects.filter(
                    game_type='constitution_challenge', 
                    is_active=True
                ).exclude(title__icontains='Advanced').first()
                context['game_level'] = 'Basic'
                context['grade_range'] = 'Grades 6-9'
            
            if game:
                context['game'] = game
            else:
                context['error'] = f'{context.get("game_level", "Constitution")} Challenge game not found'
        except Exception as e:
            context['error'] = f'Error loading Constitution Challenge: {str(e)}'
        
        # Available flag emojis
        context['flag_options'] = [
            '🇮🇳', '🏴', '🏳️', '🚩', '🏁', '🇺🇳', '🌈', '⚡', '🔥', '⭐'
        ]
        
        # Available colors
        context['color_options'] = [
            {'value': '#3B82F6', 'name': 'Blue', 'class': 'bg-blue-500'},
            {'value': '#EF4444', 'name': 'Red', 'class': 'bg-red-500'},
            {'value': '#10B981', 'name': 'Green', 'class': 'bg-green-500'},
            {'value': '#F59E0B', 'name': 'Orange', 'class': 'bg-orange-500'},
            {'value': '#8B5CF6', 'name': 'Purple', 'class': 'bg-purple-500'},
            {'value': '#EC4899', 'name': 'Pink', 'class': 'bg-pink-500'},
        ]
        
        return context
    
    def post(self, request, level=None):
        """Handle the simplified team creation and session joining/creation"""
        try:
            # Get form data
            team_name = request.POST.get('team_name', '').strip()
            country_flag = request.POST.get('country_flag', '🏴')
            country_color = request.POST.get('country_color', '#3B82F6')
            session_code = request.POST.get('session_code', '').strip().upper()
            
            # Validation
            if not team_name:
                messages.error(request, 'Team name is required')
                return redirect('group_learning:constitution_quick_start')
            
            # Get the Constitution Challenge game (avoid MultipleObjectsReturned error)
            level = level or 'basic'
            if level == 'advanced':
                game = Game.objects.filter(
                    game_type='constitution_challenge', 
                    is_active=True,
                    title__icontains='Advanced'
                ).first()
            else:
                game = Game.objects.filter(
                    game_type='constitution_challenge', 
                    is_active=True
                ).exclude(title__icontains='Advanced').first()
            
            if not game:
                messages.error(request, f'{level.title()} Constitution Challenge game not found')
                return redirect('group_learning:constitution_quick_start')
            
            # Handle session - either join existing or create new
            if session_code:
                # Try to join existing session
                try:
                    session = GameSession.objects.get(session_code=session_code)
                    if session.game != game:
                        messages.error(request, 'This session code is not for the Constitution Challenge')
                        return redirect('group_learning:constitution_quick_start')
                except GameSession.DoesNotExist:
                    messages.error(request, f'Session code {session_code} not found')
                    return redirect('group_learning:constitution_quick_start')
            else:
                # Create new session
                session = GameSession.objects.create(
                    game=game,
                    session_code=self.generate_session_code(),
                    status='waiting',
                    allow_spectators=True,
                    auto_assign_roles=True
                )
            
            # Create the team
            team = ConstitutionTeam.objects.create(
                session=session,
                team_name=team_name,
                flag_emoji=country_flag,
                country_color=country_color,
                team_avatar='🏛️',  # Default avatar for Constitution Challenge
                total_score=0,
                questions_completed=0,
            )
            
            # Start the session if it's new
            if session.status == 'waiting':
                session.status = 'active'
                session.started_at = timezone.now()
                session.save()
            
            # Redirect to gameplay
            return redirect('group_learning:constitution_game', session_code=session.session_code)
            
        except Exception as e:
            messages.error(request, f'Error creating team: {str(e)}')
            return redirect('group_learning:constitution_quick_start')
    
    def generate_session_code(self):
        """Generate a unique 6-character session code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not GameSession.objects.filter(session_code=code).exists():
                return code


class ConstitutionTeamJoinView(TemplateView):
    """Landing page for teams to join or create for Constitution Challenge"""
    template_name = 'group_learning/constitution_team_setup.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs.get('session_code')
        session = get_object_or_404(GameSession, session_code=session_code)
        
        if session.game.game_type != 'constitution_challenge':
            messages.error(self.request, 'This session is not a Constitution Challenge game.')
            return redirect('group_learning:session_detail', session_code=session_code)
        
        # Get existing teams for this session
        existing_teams = ConstitutionTeam.objects.filter(session=session).order_by('-total_score')
        
        context.update({
            'session': session,
            'game': session.game,
            'existing_teams': existing_teams,
            'team_count': existing_teams.count(),
        })
        
        return context


class ConstitutionFinalResultsView(TemplateView):
    """Final results page for Constitution Challenge games"""
    template_name = 'group_learning/constitution_final_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs.get('session_code')
        team_id = self.request.GET.get('team_id')
        
        session = get_object_or_404(GameSession, session_code=session_code)
        
        if session.game.game_type != 'constitution_challenge':
            messages.error(self.request, 'This session is not a Constitution Challenge game.')
            return redirect('group_learning:session_detail', session_code=session_code)
        
        # Get all teams for this session ordered by score
        all_teams = ConstitutionTeam.objects.filter(session=session).order_by('-total_score')
        
        # Get current team if team_id provided
        current_team = None
        if team_id:
            try:
                current_team = ConstitutionTeam.objects.get(id=team_id, session=session)
            except ConstitutionTeam.DoesNotExist:
                pass
        
        # Get team ranking
        team_ranking = None
        if current_team:
            team_ranking = list(all_teams).index(current_team) + 1
        
        # Get category breakdown for the current team
        category_breakdown = {}
        if current_team:
            # Get or create country state for scoring breakdown
            try:
                country_state = current_team.country_state
                
                # Create category breakdown for template
                category_breakdown = {
                    'democracy': {
                        'score': country_state.democracy_score,
                        'display_name': 'Democracy',
                        'emoji': '🏛️',
                        'percentage': min(100, (country_state.democracy_score / 10) * 100)
                    },
                    'fairness': {
                        'score': country_state.fairness_score,
                        'display_name': 'Fairness',
                        'emoji': '⚖️',
                        'percentage': min(100, (country_state.fairness_score / 10) * 100)
                    },
                    'freedom': {
                        'score': country_state.freedom_score,
                        'display_name': 'Freedom',
                        'emoji': '🕊️',
                        'percentage': min(100, (country_state.freedom_score / 10) * 100)
                    },
                    'stability': {
                        'score': country_state.stability_score,
                        'display_name': 'Stability',
                        'emoji': '🏗️',
                        'percentage': min(100, (country_state.stability_score / 10) * 100)
                    }
                }
            except CountryState.DoesNotExist:
                # Fallback if no country state exists
                category_breakdown = {
                    'democracy': {'score': 0, 'display_name': 'Democracy', 'emoji': '🏛️', 'percentage': 0},
                    'fairness': {'score': 0, 'display_name': 'Fairness', 'emoji': '⚖️', 'percentage': 0},
                    'freedom': {'score': 0, 'display_name': 'Freedom', 'emoji': '🕊️', 'percentage': 0},
                    'stability': {'score': 0, 'display_name': 'Stability', 'emoji': '🏗️', 'percentage': 0}
                }

        context.update({
            'session': session,
            'game': session.game,
            'team': current_team,  # Template expects 'team' not 'current_team'
            'all_teams': all_teams,
            'team_ranking': team_ranking,
            'total_teams': all_teams.count(),
            'category_breakdown': category_breakdown,
        })
        
        return context


class ConstitutionFeedbackView(View):
    """Handle feedback submissions for Constitution Challenge games"""
    
    def post(self, request, session_code):
        try:
            session = get_object_or_404(GameSession, session_code=session_code)
            
            if session.game.game_type != 'constitution_challenge':
                return JsonResponse({'error': 'Invalid session'}, status=400)
            
            # Get feedback data from request
            overall_rating = request.POST.get('overall_rating')
            game_level = request.POST.get('game_level', 'basic')  # basic or advanced
            what_learned = request.POST.get('what_learned', '')
            additional_comments = request.POST.get('additional_comments', '')
            recommend = request.POST.get('recommend', '')
            difficulty = request.POST.get('difficulty', '')
            team_id = request.POST.get('team_id')
            
            # Validate required fields
            if not overall_rating:
                return JsonResponse({'error': 'Rating is required'}, status=400)
            
            # Save to unified GameReview model
            from core.models import GameReview
            
            # Determine game type based on level
            game_type = 'constitution_advanced' if game_level == 'advanced' else 'constitution_basic'
            
            # Compile review text from various fields
            review_parts = []
            if what_learned:
                review_parts.append(f"Learning: {what_learned}")
            if recommend:
                review_parts.append(f"Recommend: {recommend}")
            if difficulty:
                review_parts.append(f"Difficulty: {difficulty}")
            if additional_comments:
                review_parts.append(f"Comments: {additional_comments}")
            
            review_text = " | ".join(review_parts) if review_parts else None
            
            # Get IP address
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].split(':')[0] or \
                        request.META.get('REMOTE_ADDR', '').split(':')[0]
            if not ip_address or ':' in ip_address:
                ip_address = '127.0.0.1'
            
            # Create or update review
            review, created = GameReview.objects.update_or_create(
                game_type=game_type,
                session_id=session_code,
                defaults={
                    'rating': int(overall_rating),
                    'review_text': review_text,
                    'ip_address': ip_address
                }
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': f'Failed to save feedback: {str(e)}'}, status=500)


class ProductionDiagnosticsAPI(View):
    """Diagnostics API to check production database schema"""
    
    def get(self, request):
        """Check actual database schema and model fields"""
        results = {
            'status': 'success',
            'database_info': {},
            'model_fields': {},
            'migration_info': {},
            'errors': []
        }
        
        try:
            from django.db import connection
            from django.db.migrations.executor import MigrationExecutor
            
            # Check migration status
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            results['migration_info']['pending_migrations'] = [
                f"{migration.app_label}.{migration.name}" for migration, _ in plan
            ]
            results['migration_info']['pending_count'] = len(plan)
            
            # Check database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                db_version = cursor.fetchone()
                results['database_info']['version'] = db_version[0]
                
                # Check if Game table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'group_learning_game'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                results['database_info']['game_table_exists'] = table_exists
                
                if table_exists:
                    # Get columns
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = 'group_learning_game'
                        ORDER BY ordinal_position;
                    """)
                    columns = cursor.fetchall()
                    results['database_info']['game_table_columns'] = [
                        {'name': col[0], 'type': col[1], 'nullable': col[2]} 
                        for col in columns
                    ]
                else:
                    results['database_info']['game_table_columns'] = []
            
            # Check Django model fields
            from .models import Game
            game_fields = [field.name for field in Game._meta.get_fields()]
            results['model_fields']['game_fields'] = game_fields
            
            # Check for mismatch if table exists
            if table_exists:
                db_column_names = [col['name'] for col in results['database_info']['game_table_columns']]
                missing_in_db = [field for field in game_fields if field not in db_column_names and not field.endswith('_set') and field not in ['learning_objectives', 'scenarios', 'sessions', 'constitution_questions']]
                missing_in_model = [col for col in db_column_names if col not in game_fields]
                
                results['model_fields']['missing_in_database'] = missing_in_db
                results['model_fields']['missing_in_model'] = missing_in_model
            
        except Exception as e:
            import traceback
            results['status'] = 'error'
            results['errors'].append(f'Database check failed: {str(e)}')
            results['errors'].append(f'Traceback: {traceback.format_exc()}')
            return JsonResponse(results, status=500)
        
        return JsonResponse(results)


class ProductionTestAPI(View):
    """Simple test API to check if deployment is working"""
    
    def get(self, request):
        """Simple test endpoint"""
        import os
        return JsonResponse({
            'status': 'success',
            'message': 'Production API is working!',
            'deployment_info': {
                'django_settings_module': os.environ.get('DJANGO_SETTINGS_MODULE', 'not set'),
                'debug': os.environ.get('DEBUG', 'not set'),
                'database_url_set': 'DATABASE_URL' in os.environ
            }
        })


class ProductionMigrateAPI(View):
    """API to run Django migrations on production"""
    
    def get(self, request):
        """Run migrations programmatically"""
        # Security check - only allow with specific token
        migrate_token = request.GET.get('migrate_token')
        if migrate_token != 'MIGRATE_PROD_2024_SECURE':
            return JsonResponse({'error': 'Invalid or missing migrate_token'}, status=403)
        
        results = {
            'status': 'success',
            'migration_results': [],
            'errors': []
        }
        
        try:
            from django.core.management import call_command
            from io import StringIO
            import sys
            
            # Capture migration output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = StringIO()
            stderr_capture = StringIO()
            
            try:
                sys.stdout = stdout_capture
                sys.stderr = stderr_capture
                
                # Run migrations
                call_command('migrate', verbosity=2, interactive=False)
                
                migration_output = stdout_capture.getvalue()
                migration_errors = stderr_capture.getvalue()
                
                results['migration_results'].append('✅ Migrations completed successfully')
                results['migration_output'] = migration_output
                if migration_errors:
                    results['migration_errors'] = migration_errors
                    
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            
        except Exception as e:
            import traceback
            results['status'] = 'error'
            results['errors'].append(f'Migration failed: {str(e)}')
            results['errors'].append(f'Traceback: {traceback.format_exc()}')
            return JsonResponse(results, status=500)
        
        return JsonResponse(results)


class ProductionSetupAPI(View):
    """API endpoint to set up production database with Constitution Challenge data"""
    
    def get(self, request):
        # Security check - only allow in specific conditions
        setup_token = request.GET.get('setup_token')
        if setup_token != 'decipherworld-setup-2025':
            return JsonResponse({
                'error': 'Unauthorized', 
                'hint': 'Add ?setup_token=decipherworld-setup-2025 to the URL'
            }, status=403)
        
        # Check if this is a request for specific actions
        action = request.GET.get('action')
        if action == 'update_advanced_questions':
            return self.update_advanced_questions()
        elif action == 'create_advanced_game':
            return self.create_advanced_game()
        elif action == 'create_learning_modules':
            return self.create_learning_modules()
        elif action == 'check_questions':
            return self.check_questions()
        elif action == 'setup_climate_game':
            return self.setup_climate_game()
        elif action == 'populate_climate_scenarios':
            return self.populate_climate_scenarios_only()
        
        try:
            results = {
                'status': 'starting',
                'steps_completed': [],
                'errors': []
            }
            
            # Step 1: Run all available migrations
            try:
                # Run all group_learning migrations to ensure schema is complete
                call_command('migrate', 'group_learning', verbosity=0, interactive=False)
                results['steps_completed'].append('✅ All database migrations completed')
                
                # Then run core app migrations if needed
                try:
                    call_command('migrate', 'core', verbosity=0, interactive=False)
                    call_command('migrate', 'games', verbosity=0, interactive=False)
                    call_command('migrate', 'robotic_buddy', verbosity=0, interactive=False)
                    results['steps_completed'].append('✅ Other app migrations completed')
                except Exception:
                    results['steps_completed'].append('⚠️ Some app migrations skipped (non-critical)')
                    
            except Exception as e:
                # If even basic migrations fail, try to create tables manually
                results['errors'].append(f'⚠️ Migration warning: {str(e)}')
                results['steps_completed'].append('⚠️ Will proceed with manual table creation if needed')
            
            # Step 2: Create superuser if needed
            try:
                User = get_user_model()
                if not User.objects.filter(username='admin').exists():
                    User.objects.create_superuser(
                        username='admin', 
                        email='admin@decipherworld.com', 
                        password='DecipherWorld2025!'
                    )
                    results['steps_completed'].append('✅ Superuser created (admin/DecipherWorld2025!)')
                else:
                    results['steps_completed'].append('✅ Superuser already exists')
            except Exception as e:
                results['errors'].append(f'❌ Superuser creation error: {str(e)}')
            
            # Step 3: Set up Constitution Challenge using management command (safer approach)  
            try:
                # Check if tables exist first
                try:
                    Game.objects.exists()
                    results['steps_completed'].append('✅ Database tables are accessible')
                except Exception as table_error:
                    results['errors'].append(f'❌ Database tables not ready: {str(table_error)}')
                    return JsonResponse(results, status=500)
                
                # Use management command to create Constitution game (much safer)
                try:
                    from io import StringIO
                    import sys
                    
                    # Check if game already exists
                    try:
                        existing_game = Game.objects.filter(
                            title='Build Your Country: The Constitution Challenge'
                        ).first()
                        if existing_game:
                            results['steps_completed'].append('✅ Constitution Challenge game already exists')
                            constitution_game = existing_game
                        else:
                            raise Game.DoesNotExist()
                    except Game.DoesNotExist:
                        # Capture management command output
                        old_stdout = sys.stdout
                        stdout_capture = StringIO()
                        sys.stdout = stdout_capture
                        
                        try:
                            # Run the simple constitution setup management command
                            call_command('create_constitution_simple')
                            command_output = stdout_capture.getvalue()
                            results['steps_completed'].append('✅ Constitution Challenge created via simple management command')
                            results['command_output'] = command_output[:1000]  # Limit output size
                            
                            # Get the created game
                            constitution_game = Game.objects.filter(
                                title='Build Your Country: The Constitution Challenge'
                            ).first()
                            
                        finally:
                            sys.stdout = old_stdout
                
                    # Create demo session  
                    from .models import GameSession
                    demo_session, session_created = GameSession.objects.get_or_create(
                        session_code='CONST2024',
                        defaults={
                            'game': constitution_game,
                            'status': 'waiting'
                        }
                    )
                    
                    if session_created:
                        results['steps_completed'].append('✅ Demo session CONST2024 created')
                    else:
                        results['steps_completed'].append('✅ Demo session CONST2024 already exists')
                        
                    # Verify questions exist
                    question_count = ConstitutionQuestion.objects.filter(game=constitution_game).count()
                    results['steps_completed'].append(f'✅ Final verification: Game "{constitution_game.title}" with {question_count} questions')
                    
                except Exception as create_error:
                    results['errors'].append(f'⚠️ Game creation failed: {str(create_error)}')
                    return JsonResponse(results, status=500)
                
            except Exception as e:
                import traceback
                results['errors'].append(f'❌ Constitution setup error: {str(e)}')
                results['errors'].append(f'❌ Full error: {traceback.format_exc()}')
            
            # Final status
            results['status'] = 'completed' if not results['errors'] else 'completed_with_errors'
            results['next_steps'] = [
                '🌐 Visit: https://decipherworld-app.azurewebsites.net/learn/',
                '🏛️ Start Constitution Challenge game',
                '👤 Admin panel: https://decipherworld-app.azurewebsites.net/admin/'
            ]
            
            return JsonResponse(results)
            
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'error': str(e),
                'steps_completed': results.get('steps_completed', []),
                'errors': results.get('errors', []) + [f'❌ Setup failed: {str(e)}']
            }, status=500)
    
    def update_advanced_questions(self):
        """Update Advanced Constitution Challenge with sophisticated questions"""
        try:
            from django.db import transaction
            
            results = {
                'status': 'success',
                'steps_completed': [],
                'errors': []
            }
            
            with transaction.atomic():
                # Get the Advanced Constitution Game
                game = Game.objects.filter(
                    title="Advanced Constitution Challenge",
                    game_type='constitution_challenge',
                    is_active=True
                ).first()
                
                if not game:
                    results['errors'].append('❌ Advanced Constitution Game not found! Run create_advanced_constitution_game first.')
                    return JsonResponse(results, status=404)
                
                results['steps_completed'].append(f'✅ Found Advanced Constitution Game (ID: {game.id})')
                
                # Clear existing questions
                existing_count = ConstitutionQuestion.objects.filter(game=game).count()
                if existing_count > 0:
                    results['steps_completed'].append(f'🔄 Clearing {existing_count} existing questions...')
                    ConstitutionQuestion.objects.filter(game=game).delete()
                
                # Run the management command to update questions
                try:
                    from django.core.management import call_command
                    call_command('update_advanced_constitution_questions')
                    results['steps_completed'].append('✅ Advanced Constitution questions updated successfully')
                    
                    # Verify questions were created
                    new_count = ConstitutionQuestion.objects.filter(game=game).count()
                    results['steps_completed'].append(f'✅ Verification: {new_count} sophisticated questions created')
                    
                    return JsonResponse(results)
                    
                except Exception as cmd_error:
                    results['errors'].append(f'❌ Management command failed: {str(cmd_error)}')
                    return JsonResponse(results, status=500)
                    
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'error': f'Advanced questions update failed: {str(e)}'
            }, status=500)
    
    def create_advanced_game(self):
        """Create Advanced Constitution Challenge game"""
        try:
            from django.db import transaction
            
            results = {
                'status': 'success',
                'steps_completed': [],
                'errors': []
            }
            
            with transaction.atomic():
                # Create Advanced Constitution Game
                game, created = Game.objects.get_or_create(
                    title="Advanced Constitution Challenge",
                    defaults={
                        'subtitle': 'Advanced Governance and Constitutional Analysis (Grades 9-12)',
                        'game_type': 'constitution_challenge',
                        'description': 'Test your advanced understanding of constitutional principles, governance systems, and democratic institutions through complex scenarios and comparative analysis.',
                        'context': 'Dive deep into advanced constitutional concepts including federalism, judicial review, electoral systems, and emergency powers. Compare Indian constitutional provisions with other major democracies.',
                        'min_players': 2,
                        'max_players': 8,
                        'estimated_duration': 45,
                        'target_age_min': 14,
                        'target_age_max': 18,
                        'difficulty_level': 3,  # Advanced
                        'introduction_text': 'Welcome to the Advanced Constitution Challenge! You will face complex governance scenarios that test your understanding of constitutional principles, democratic institutions, and comparative government systems. Each decision will shape your nation\'s development and democratic health.',
                        'is_active': True
                    }
                )
                
                if created:
                    results['steps_completed'].append(f'✅ Created Advanced Constitution Game (ID: {game.id})')
                else:
                    results['steps_completed'].append(f'✅ Advanced Constitution Game already exists (ID: {game.id})')
                    
                results['steps_completed'].append(f'🎉 Advanced Constitution Challenge ready!')
                results['steps_completed'].append(f'📊 Game ID: {game.id}')
                results['steps_completed'].append(f'🎯 Target: Grades 9-12 (Advanced)')
                
                return JsonResponse(results)
                    
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'error': f'Advanced game creation failed: {str(e)}'
            }, status=500)
    
    def create_learning_modules(self):
        """Create learning modules for both Basic and Advanced Constitution games"""
        try:
            from django.core.management import call_command
            from io import StringIO
            import sys
            
            results = {
                'status': 'success',
                'steps_completed': [],
                'errors': []
            }
            
            # Create basic learning modules first
            try:
                old_stdout = sys.stdout
                stdout_capture = StringIO()
                sys.stdout = stdout_capture
                
                call_command('populate_learning_modules')
                command_output = stdout_capture.getvalue()
                
                sys.stdout = old_stdout
                
                results['steps_completed'].append('✅ Created basic learning modules for Constitution Challenge')
                results['steps_completed'].append(f'📊 Basic modules output: {command_output[:200]}...')
                
            except Exception as e:
                results['errors'].append(f'⚠️ Basic learning modules error: {str(e)}')
            
            # Create advanced learning modules
            try:
                old_stdout = sys.stdout
                stdout_capture = StringIO()
                sys.stdout = stdout_capture
                
                call_command('create_advanced_learning_modules')
                command_output = stdout_capture.getvalue()
                
                sys.stdout = old_stdout
                
                results['steps_completed'].append('✅ Created advanced learning modules for Advanced Constitution Challenge')
                results['steps_completed'].append(f'📚 Advanced modules: 64 choice-specific modules created')
                
            except Exception as e:
                results['errors'].append(f'⚠️ Advanced learning modules error: {str(e)}')
            
            # Verify modules were created
            try:
                from .models import GameLearningModule
                basic_count = GameLearningModule.objects.filter(game_type='constitution_challenge', trigger_condition='topic_based').count()
                advanced_count = GameLearningModule.objects.filter(game_type='constitution_challenge', trigger_condition='option_based').count()
                
                results['steps_completed'].append(f'✅ Verification: {basic_count} basic + {advanced_count} advanced learning modules')
                
            except Exception as e:
                results['errors'].append(f'⚠️ Verification error: {str(e)}')
            
            return JsonResponse(results)
                    
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'error': f'Learning modules creation failed: {str(e)}'
            }, status=500)
    
    def check_questions(self):
        """Debug method to check what questions are in both Basic and Advanced games"""
        try:
            results = {
                'status': 'success',
                'games': [],
                'errors': []
            }
            
            # Get all constitution challenge games
            games = Game.objects.filter(game_type='constitution_challenge', is_active=True)
            
            for game in games:
                questions = ConstitutionQuestion.objects.filter(game=game).order_by('order')
                game_data = {
                    'game_id': game.id,
                    'game_title': game.title,
                    'question_count': questions.count(),
                    'questions': []
                }
                
                for q in questions[:3]:  # Show first 3 questions for debugging
                    game_data['questions'].append({
                        'order': q.order,
                        'category': q.category,
                        'question_preview': q.question_text[:100] + "..." if len(q.question_text) > 100 else q.question_text,
                        'options_count': q.options.count()
                    })
                
                results['games'].append(game_data)
            
            return JsonResponse(results)
                    
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'error': f'Questions check failed: {str(e)}'
            }, status=500)
    
    def setup_climate_game(self):
        """Set up Climate Crisis India game with all required tables and data"""
        try:
            from django.db import transaction
            from django.core.management import call_command
            from io import StringIO
            import sys
            
            results = {
                'status': 'success',
                'steps_completed': [],
                'errors': []
            }
            
            with transaction.atomic():
                # Step 1: Ensure Climate game tables exist (force migration)
                try:
                    # Try to fake problematic migrations that already exist in production
                    problematic_migrations = ['0007', '0008']  # These add columns that already exist
                    for migration in problematic_migrations:
                        try:
                            call_command('migrate', 'group_learning', migration, fake=True, verbosity=0)
                            results['steps_completed'].append(f'✅ Faked problematic migration {migration}')
                        except Exception:
                            results['steps_completed'].append(f'⚠️ Migration {migration} fake attempt skipped')
                    
                    # Now run the climate game migrations (should apply 0009-0012)
                    call_command('migrate', 'group_learning', verbosity=0, interactive=False)
                    results['steps_completed'].append('✅ Climate game migrations completed')
                    
                except Exception as e:
                    results['errors'].append(f'⚠️ Migration issue: {str(e)}')
                    # Continue anyway - tables might already exist
                
                # Step 2: Verify climate game tables exist
                try:
                    from .models import ClimateGame, ClimateScenario, ClimateQuestion
                    ClimateGame.objects.exists()  # This will fail if table doesn't exist
                    results['steps_completed'].append('✅ Climate game tables verified')
                except Exception as e:
                    results['errors'].append(f'❌ Climate game tables missing: {str(e)}')
                    return JsonResponse(results, status=500)
                
                # Step 3: Create Climate Crisis India game
                try:
                    from .models import Game, ClimateGame
                    
                    # Check if climate game already exists
                    climate_game = Game.objects.filter(
                        title='Climate Crisis India – Monsoon Mayhem',
                        game_type='environmental'
                    ).first()
                    
                    if not climate_game:
                        # Create the climate game with all required base Game fields
                        climate_game = ClimateGame.objects.create(
                            title='Climate Crisis India – Monsoon Mayhem',
                            subtitle='Role-playing simulation for climate education',
                            description='Students take on different roles to make decisions during India\'s climate crises. Experience real trade-offs between economic growth, environmental protection, and social needs.',
                            context='India faces mounting climate challenges including air pollution, floods, droughts, and extreme weather. Students explore policy decisions from multiple stakeholder perspectives.',
                            game_type='environmental',  # Use existing environmental game type
                            is_active=True,
                            # Base Game configuration fields (required)
                            min_players=5,
                            max_players=35,
                            estimated_duration=45,  # 45 minutes
                            target_age_min=12,      # Grade 7+
                            target_age_max=18,      # Grade 12
                            difficulty_level=2,     # Intermediate
                            # Climate-specific meters
                            climate_resilience_meter=50,
                            gdp_meter=50,
                            public_morale_meter=50,
                            environmental_health_meter=50
                        )
                        results['steps_completed'].append('✅ Climate Crisis India game created')
                    else:
                        results['steps_completed'].append('✅ Climate Crisis India game already exists')
                    
                except Exception as e:
                    results['errors'].append(f'❌ Climate game creation failed: {str(e)}')
                    return JsonResponse(results, status=500)
                
                # Step 4: Populate scenarios and questions
                try:
                    # Capture management command output
                    old_stdout = sys.stdout
                    stdout_capture = StringIO()
                    sys.stdout = stdout_capture
                    
                    try:
                        call_command('populate_climate_scenarios')
                        command_output = stdout_capture.getvalue()
                        results['steps_completed'].append('✅ Climate scenarios and questions populated')
                        
                        # Show summary of what was created
                        scenario_count = ClimateScenario.objects.filter(game=climate_game).count()
                        question_count = ClimateQuestion.objects.filter(scenario__game=climate_game).count()
                        results['steps_completed'].append(f'✅ Created {scenario_count} scenarios with {question_count} role-specific questions')
                        
                    finally:
                        sys.stdout = old_stdout
                        
                except Exception as e:
                    results['errors'].append(f'⚠️ Scenario population issue: {str(e)}')
                    # This is non-critical - game can work without scenarios initially
                
                # Step 5: Create test session
                try:
                    from .models import GameSession, ClimateGameSession
                    
                    test_session, created = GameSession.objects.get_or_create(
                        session_code='CLIMATE2024',
                        defaults={
                            'game': climate_game,
                            'status': 'waiting'
                        }
                    )
                    
                    if created:
                        # Create the climate-specific session extension
                        ClimateGameSession.objects.create(
                            gamesession_ptr=test_session,
                            climate_game=climate_game,
                            current_round=1,
                            current_phase='lobby'
                        )
                        results['steps_completed'].append('✅ Test session CLIMATE2024 created')
                    else:
                        results['steps_completed'].append('✅ Test session CLIMATE2024 already exists')
                        
                except Exception as e:
                    results['errors'].append(f'⚠️ Test session creation issue: {str(e)}')
                
                # Final verification
                try:
                    climate_count = ClimateGame.objects.count()
                    results['steps_completed'].append(f'✅ Final verification: {climate_count} climate game(s) ready')
                    
                except Exception as e:
                    results['errors'].append(f'⚠️ Verification error: {str(e)}')
            
            results['next_steps'] = [
                '🌍 Visit: https://decipherworld-app.azurewebsites.net/learn/climate/',
                '🎮 Test Mode: Create a session and test the game',
                '👤 Admin: https://decipherworld-app.azurewebsites.net/admin/'
            ]
            
            return JsonResponse(results)
                    
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'error': f'Climate game setup failed: {str(e)}'
            }, status=500)
    
    def populate_climate_scenarios_only(self):
        """Just run the populate climate scenarios management command"""
        try:
            from django.core.management import call_command
            from io import StringIO
            import sys
            
            results = {
                'status': 'success',
                'steps_completed': [],
                'errors': []
            }
            
            # Capture command output
            old_stdout = sys.stdout
            stdout_capture = StringIO()
            sys.stdout = stdout_capture
            
            try:
                # Run the populate command
                call_command('populate_climate_scenarios')
                command_output = stdout_capture.getvalue()
                results['steps_completed'].append('✅ Climate scenarios populated via management command')
                results['command_output'] = command_output
                
            finally:
                sys.stdout = old_stdout
            
            return JsonResponse(results)
                    
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'error': f'Climate scenarios population failed: {str(e)}'
            }, status=500)


# ==================================================================================
# DESIGN THINKING / CLASSROOM INNOVATORS CHALLENGE VIEWS
# ==================================================================================




class DesignThinkingJoinView(TemplateView):
    """Student session joining page"""
    template_name = 'group_learning/design_thinking/join_session.html'
    
    def _handle_error(self, request, message, field=None):
        """Handle error response - AJAX or redirect"""
        is_ajax = (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            'application/json' in request.headers.get('Accept', '') or
            request.headers.get('Content-Type', '').startswith('multipart/form-data')
        )
        
        if is_ajax:
            return JsonResponse({
                'success': False,
                'error': message,
                'field': field
            }, status=400)
        else:
            messages.error(request, message)
            return redirect('group_learning:create_simplified_session')
    
    def post(self, request):
        """Handle student session joining"""
        session_code = request.POST.get('session_code', '').strip().upper()
        team_name = request.POST.get('team_name', '').strip()
        team_emoji = request.POST.get('team_emoji', '💡')
        team_members_json = request.POST.get('team_members', '[]')
        
        if not session_code:
            return self._handle_error(request, 'Session code is required', 'session_code')
            
        if not team_name:
            return self._handle_error(request, 'Team name is required', 'team_name')
        
        # Parse and validate team members
        try:
            team_members = json.loads(team_members_json) if team_members_json else []
            if not isinstance(team_members, list):
                team_members = []
        except (json.JSONDecodeError, TypeError):
            team_members = []
        
        # Team members are optional metadata for simplified flow
        team_members = [member.strip() for member in team_members if member.strip()]
        
        # No validation required - team members are just metadata
        
        # Get the simplified Design Thinking game
        try:
            design_game = DesignThinkingGame.objects.filter(
                auto_advance_enabled=True
            ).first()
            
            if not design_game:
                return self._handle_error(request, 'Simplified Design Thinking game not found. Please refresh and try again.')
        except Exception as e:
            return self._handle_error(request, 'Design Thinking game not found. Please refresh and try again.')
        
        # Find and validate session
        try:
            session = DesignThinkingSession.objects.get(session_code=session_code)
            # Check if session uses any simplified game (auto_advance_enabled=True)
            if not session.design_game or not session.design_game.auto_advance_enabled:
                return self._handle_error(request, 'This session code is not for the Simplified Design Thinking game', 'session_code')
            
            # Check session status
            if session.status == 'completed':
                return self._handle_error(request, 'This session has already been completed', 'session_code')
            elif session.status == 'abandoned':
                return self._handle_error(request, 'This session is no longer active', 'session_code')
            
            # Check team limit (100 teams maximum)
            current_team_count = session.design_teams.count()
            if current_team_count >= 100:
                return self._handle_error(request, 'This session is full (maximum 100 teams)', 'session_code')
                
        except DesignThinkingSession.DoesNotExist:
            return self._handle_error(request, f'Session code {session_code} not found', 'session_code')
        
        # Check for duplicate team name in session
        if DesignTeam.objects.filter(session=session, team_name=team_name).exists():
            return self._handle_error(request, f'Team name "{team_name}" is already taken. Please choose a different name.', 'team_name')
        
        # Create team with members
        team = DesignTeam.objects.create(
            session=session,
            team_name=team_name,
            team_emoji=team_emoji,
            team_members=team_members
        )
        
        # Create TeamProgress records for all missions up to current mission
        import logging
        logger = logging.getLogger(__name__)
        
        # Get all missions in order
        all_missions = session.design_game.missions.filter(is_active=True).order_by('order')
        
        if session.current_mission:
            # Create progress records for all missions up to and including current mission
            for mission in all_missions:
                progress, created = TeamProgress.objects.get_or_create(
                    session=session,
                    team=team,
                    mission=mission
                )
                if created:
                    logger.info(f"Created TeamProgress for new team {team.team_name} on mission {mission.title}")
                
                # Stop at current mission - don't create progress for future missions
                if mission.id == session.current_mission.id:
                    break
        else:
            # If no current mission, session hasn't started yet - don't create any progress records
            logger.info(f"Session {session.session_code} has no current mission - progress records will be created when session starts")
        
        # Store team info in Django session
        request.session['design_team_id'] = team.id
        request.session['design_session_code'] = session.session_code
        request.session['is_facilitator'] = False
        
        # Broadcast team join to all connected clients via WebSocket
        self._broadcast_team_joined(session.session_code, team)
        
        messages.success(request, f'Successfully joined session! Welcome, Team {team_name} {team_emoji}')
        return redirect('group_learning:simplified_student_dashboard', session_code=session.session_code)
    
    def _broadcast_team_joined(self, session_code, team):
        """Broadcast team join event to all connected clients"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from django.utils import timezone
        
        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f'design_thinking_{session_code}'
            team_data = {
                'id': team.id,
                'name': team.team_name,
                'emoji': team.team_emoji,
                'color': team.team_color,
                'members': team.team_members or []
            }
            
            # Get updated session status including new team count
            session_data = self._get_session_status_data(session_code)
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'team_joined',
                    'team_data': team_data,
                    'session_data': session_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    def _get_session_status_data(self, session_code):
        """Get current session status data for broadcasting"""
        try:
            from .models import DesignThinkingSession
            session = DesignThinkingSession.objects.select_related('current_mission').get(session_code=session_code)
            
            # Get teams and their progress
            teams_data = []
            for team in session.design_teams.all():
                teams_data.append({
                    'id': team.id,
                    'name': team.team_name,
                    'emoji': team.team_emoji,
                    'color': team.team_color,
                    'missions_completed': team.missions_completed,
                    'total_submissions': team.total_submissions,
                    'progress_percentage': team.get_progress_percentage()
                })
            
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
                'mission_progress': session.get_mission_progress(),
                'session_started': session.started_at.isoformat() if session.started_at else None,
                'mission_started': session.mission_start_time.isoformat() if session.mission_start_time else None
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting session status data: {str(e)}")
            return {'error': 'Status retrieval failed'}


@method_decorator(csrf_exempt, name='dispatch')
class ValidateSessionView(View):
    """API endpoint to validate session code and return session information"""
    
    def post(self, request):
        """Validate session code and return session info"""
        session_code = request.POST.get('session_code', '').strip().upper()
        
        if not session_code or len(session_code) != 6:
            return JsonResponse({'valid': False, 'error': 'Invalid session code format'})
        
        try:
            session = DesignThinkingSession.objects.get(session_code=session_code)
            
            # Check session status
            if session.status in ['completed', 'abandoned']:
                return JsonResponse({'valid': False, 'error': 'Session is no longer active'})
            
            # Return session information
            return JsonResponse({
                'valid': True,
                'school_name': session.school_name or '',
                'grade_level': session.grade_level or '',
                'session_code': session.session_code,
                'current_teams': session.design_teams.count()
            })
            
        except DesignThinkingSession.DoesNotExist:
            return JsonResponse({'valid': False, 'error': 'Session not found'})


# ==================================================================================
# SIMPLIFIED DESIGN THINKING VIEWS (Auto-Progression)
# ==================================================================================

class SimplifiedStudentDashboardView(TemplateView):
    """
    Simplified student dashboard for auto-progression Design Thinking sessions.
    
    Key features:
    - Auto-starts sessions without teacher dependency
    - Skips kickoff/intro phases to prevent students getting stuck
    - Automatically advances from kickoff to empathy phase
    - Provides streamlined input forms for each design thinking phase
    """
    template_name = 'group_learning/design_thinking/simplified_student_dashboard.html'
    
    def get_context_data(self, **kwargs):
        logger = logging.getLogger(__name__)  # Define logger in method scope
        logger.info(f"🎯 SimplifiedStudentDashboardView.get_context_data called with kwargs: {kwargs}")
        context = super().get_context_data(**kwargs)
        
        session_code = kwargs.get('session_code')
        if not session_code:
            logger.error("No session code provided to SimplifiedStudentDashboardView")
            context['error'] = 'Session code is required'
            return context
            
        try:
            session = DesignThinkingSession.objects.select_related(
                'design_game', 'current_mission'
            ).get(session_code=session_code)
            
            # Validate session is configured for simplified mode
            # Check if session has required data (DesignThinkingSession doesn't have is_active field)
            if not session.design_game:
                context['error'] = 'This session is not properly configured'
                return context
                
            if not getattr(session.design_game, 'auto_advance_enabled', False):
                logger.warning(f"Session {session_code} accessed on simplified dashboard but auto-advance is disabled")
                context['warning'] = 'This session may not support auto-progression'
            
            # Auto-start simplified sessions (no teacher dependency)
            if session.status == 'waiting' and not session.is_facilitator_controlled:
                session.status = 'in_progress'
                session.started_at = timezone.now()
                
                # Set the first REAL mission (skip kickoff/intro phases)
                if not session.current_mission:
                    first_mission = session.design_game.missions.filter(
                        is_active=True
                    ).exclude(mission_type='kickoff').order_by('order').first()
                    if first_mission:
                        session.current_mission = first_mission
                        session.mission_start_time = timezone.now()
                        logger.info(f"Set first real mission for session {session_code}: {first_mission.title} (skipped kickoff)")
                
                session.save()
                logger.info(f"Auto-started simplified session {session_code}")
            
            # Handle case where session is in progress but has no current mission (repair broken sessions)
            elif session.status == 'in_progress' and not session.current_mission:
                first_mission = session.design_game.missions.filter(
                    is_active=True
                ).exclude(mission_type='kickoff').order_by('order').first()
                if first_mission:
                    session.current_mission = first_mission
                    session.mission_start_time = timezone.now()
                    session.save()
                    logger.info(f"Repaired session {session_code}: Set missing current_mission to {first_mission.title} (skipped kickoff)")
            
            # FIXED: Auto-advance if stuck on kickoff phase
            elif session.status == 'in_progress' and session.current_mission and session.current_mission.mission_type == 'kickoff':
                next_mission = session.design_game.missions.filter(
                    is_active=True,
                    mission_type='empathy'
                ).order_by('order').first()
                if next_mission:
                    session.current_mission = next_mission
                    session.mission_start_time = timezone.now()
                    session.save()
                    logger.info(f"Auto-advanced session {session_code} from kickoff to: {next_mission.title}")
            
            # Get or create team for this student
            try:
                team = self._get_or_create_student_team(session)
                
                # Ensure TeamProgress records exist for current mission (repair existing teams)
                if session.current_mission:
                    logger.info(f"🔧 About to call _ensure_team_progress_exists for team {team.team_name}")
                    self._ensure_team_progress_exists(team, session)
                else:
                    logger.warning(f"🔧 No current mission for session {session.session_code}, skipping TeamProgress creation")
                    
            except Exception as e:
                logger.error(f"Error getting/creating team for session {session_code}: {str(e)}")
                context['error'] = 'Unable to join or create team. Please try again.'
                return context
            
            logger.info(f"✅ Student dashboard loaded for session {session_code}, team {team.team_name}, mission: {session.current_mission.mission_type if session.current_mission else 'None'}")

            context.update({
                'session': session,
                'team': team,
                'current_mission': session.current_mission,
                'game_config': {
                    'auto_advance_enabled': session.design_game.auto_advance_enabled,
                    'completion_threshold': session.design_game.completion_threshold_percentage,
                    'phase_transition_delay': session.design_game.phase_transition_delay,
                    'scoring_system': getattr(session.design_game, 'scoring_system', 'numeric')
                }
            })
            
        except DesignThinkingSession.DoesNotExist:
            logger.warning(f"Attempted access to non-existent session: {session_code}")
            context['error'] = f'Session {session_code} not found. Please check the session code.'
        except Exception as e:
            logger.error(f"Error loading simplified student dashboard: {str(e)}", exc_info=True)
            context['error'] = 'Unable to load session data. Please try again later.'
            
        return context
    
    def _get_or_create_student_team(self, session):
        """Get existing team or create new one for student - SIMPLIFIED"""
        import logging
        from django.db import transaction
        logger = logging.getLogger(__name__)
        
        # SIMPLE: Get the first team for this session, or create if none exists
        try:
            team = DesignTeam.objects.filter(session=session).first()
            if team:
                logger.info(f"Found existing team: {team.team_name} (ID: {team.id})")
                return team
                
            # No team exists, create one
            with transaction.atomic():
                team = DesignTeam.objects.create(
                    session=session,
                    team_name='Team Alpha',
                    team_emoji='🚀',
                    team_members=[]
                )
                logger.info(f"Created new team: {team.team_name} (ID: {team.id})")
                return team
                
        except Exception as e:
            logger.error(f"Error with team for session {session.session_code}: {str(e)}")
            raise
    
    def _ensure_team_progress_exists(self, team, session):
        """Ensure TeamProgress records exist for team up to current mission"""
        logger = logging.getLogger(__name__)
        logger.info(f"🔧 _ensure_team_progress_exists called for team {team.team_name} in session {session.session_code}")
        try:
            from .models import TeamProgress
            
            if not session.current_mission:
                return
            
            # Get all missions up to and including current mission
            current_mission_order = session.current_mission.order
            missions_up_to_current = session.design_game.missions.filter(
                is_active=True, 
                order__lte=current_mission_order
            ).order_by('order')
            
            # Create TeamProgress records for missing missions
            created_count = 0
            for mission in missions_up_to_current:
                progress, created = TeamProgress.objects.get_or_create(
                    session=session,
                    team=team,
                    mission=mission,
                    defaults={
                        'is_completed': False,
                        'submission_count': 0
                    }
                )
                if created:
                    created_count += 1
            
            if created_count > 0:
                logger.info(f"Created {created_count} TeamProgress records for team {team.team_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring team progress exists: {str(e)}")
            # Don't raise - this is a repair operation, shouldn't break the main flow


class SimplifiedTeacherDashboardView(TemplateView):
    """
    Simplified teacher dashboard for real-time scoring and oversight
    Shows live team progress and enables quick scoring
    """
    template_name = 'group_learning/design_thinking/whatsapp_teacher_dashboard.html'
    
    def get_context_data(self, **kwargs):
        logger = logging.getLogger(__name__)  # Define logger in method scope
        context = super().get_context_data(**kwargs)
        
        session_code = kwargs.get('session_code')
        if not session_code:
            logger.error("No session code provided to SimplifiedTeacherDashboardView")
            context['error'] = 'Session code is required'
            return context
            
        try:
            session = DesignThinkingSession.objects.select_related(
                'design_game', 'current_mission', 'facilitator'
            ).prefetch_related(
                'design_teams',
                'all_inputs__team',
                'completion_tracking__team'
            ).get(session_code=session_code)
            
            # Validate session state (DesignThinkingSession doesn't have is_active field)
            # Check if session is accessible by verifying it has required data
            if not session.design_game:
                context['error'] = 'This session is not properly configured'
                return context
                
            # Verify teacher access (optional - could add permission checks here)
            if self.request.user.is_authenticated and session.facilitator:
                if session.facilitator != self.request.user:
                    logger.warning(f"User {self.request.user} accessing session {session_code} not facilitated by them")
                    context['warning'] = 'You are not the original facilitator of this session'
                    
            try:
                session_stats = self._get_session_stats(session)
            except Exception as e:
                logger.error(f"Error calculating session stats for {session_code}: {str(e)}")
                session_stats = {'error': 'Unable to calculate session statistics'}
            
            # Get submission review data for simplified system
            from .models import SimplifiedPhaseInput
            
            # Get all submissions for this session (use SimplifiedPhaseInput for simplified system)
            all_submissions = SimplifiedPhaseInput.objects.filter(
                team__session=session
            ).select_related('team', 'mission').order_by('submitted_at')
            
            # Get unscored submissions
            unscored_submissions = all_submissions.filter(
                teacher_score__isnull=True
            )
            
            # Get current submission to review (first unscored)
            current_submission = unscored_submissions.first()
            
            # Calculate scoring progress
            total_submissions = all_submissions.count()
            scored_submissions = all_submissions.filter(
                teacher_score__isnull=False
            ).count()
            
            scoring_progress = {
                'scored': scored_submissions,
                'total': total_submissions,
                'percentage': round((scored_submissions / total_submissions * 100), 1) if total_submissions > 0 else 0,
                'remaining': total_submissions - scored_submissions
            }
            
            # Organize submissions by team for template (JSON-serializable)
            team_submissions = {}
            for team in session.design_teams.all():
                team_submissions_list = all_submissions.filter(team=team).order_by('-submitted_at')
                latest_submission = team_submissions_list.first()
                
                latest_submission_data = None
                if latest_submission:
                    latest_submission_data = {
                        'id': latest_submission.id,
                        'mission_title': latest_submission.mission.title if latest_submission.mission else 'Current Phase',
                        'submission_data': latest_submission.input_data or 'No data',
                        'submitted_at': latest_submission.submitted_at.isoformat(),
                        'teacher_score': latest_submission.teacher_score
                    }
                
                team_submissions[team.id] = {
                    'latest_submission': latest_submission_data,
                    'submission_count': team_submissions_list.count(),
                    'submissions': []  # Simplified for JSON
                }

            # Get teams with safety check
            teams = list(session.design_teams.all())

            logger.info(f"✅ Teacher dashboard loaded for session {session_code}: {len(teams)} teams, {all_submissions.count()} submissions")

            context.update({
                'session': session,
                'teams': teams,
                'current_mission': session.current_mission,
                'game_config': {
                    'auto_advance_enabled': session.design_game.auto_advance_enabled,
                    'completion_threshold': session.design_game.completion_threshold_percentage,
                    'scoring_system': getattr(session.design_game, 'scoring_system', 'numeric')
                },
                'session_stats': session_stats,
                # Submission review data
                'all_submissions': all_submissions,
                'unscored_submissions': unscored_submissions,
                'current_submission': current_submission,
                'scoring_progress': scoring_progress,
                'team_submissions': team_submissions,
                'team_submissions_json': json.dumps(team_submissions)
            })
            
        except DesignThinkingSession.DoesNotExist:
            logger.warning(f"Teacher attempted access to non-existent session: {session_code}")
            context['error'] = f'Session {session_code} not found. Please verify the session code.'
        except Exception as e:
            logger.error(f"Error loading simplified teacher dashboard: {str(e)}", exc_info=True)
            context['error'] = 'Unable to load session data. Please try again later.'
            
        return context
    
    def _get_session_stats(self, session):
        """Get session statistics for teacher dashboard with error handling"""
        try:
            total_teams = session.design_teams.count()
            
            # Initialize default stats
            completion_stats = {
                'total_teams': total_teams, 
                'completed_teams': 0, 
                'in_progress_teams': 0,
                'completion_percentage': 0.0
            }
            
            if session.current_mission and total_teams > 0:
                from .models import PhaseCompletionTracker
                
                try:
                    completed_teams = PhaseCompletionTracker.objects.filter(
                        session=session,
                        mission=session.current_mission,
                        is_ready_to_advance=True
                    ).count()
                    
                    in_progress_teams = PhaseCompletionTracker.objects.filter(
                        session=session,
                        mission=session.current_mission,
                        is_ready_to_advance=False,
                        completed_inputs__gt=0
                    ).count()
                    
                    completion_percentage = (completed_teams / total_teams) * 100 if total_teams > 0 else 0
                    
                    completion_stats.update({
                        'completed_teams': completed_teams,
                        'in_progress_teams': in_progress_teams,
                        'completion_percentage': round(completion_percentage, 1)
                    })
                    
                except Exception as e:
                    logger.error(f"Error calculating completion stats: {str(e)}")
                    completion_stats['error'] = 'Unable to calculate completion statistics'
            
            # Add recent activity stats
            try:
                from django.utils import timezone
                from datetime import timedelta
                
                recent_cutoff = timezone.now() - timedelta(minutes=5)
                recent_submissions = session.all_inputs.filter(
                    submitted_at__gte=recent_cutoff
                ).count()
                
                completion_stats['recent_activity'] = {
                    'submissions_last_5min': recent_submissions,
                    'active_session': recent_submissions > 0
                }
                
            except Exception as e:
                logger.error(f"Error calculating recent activity: {str(e)}")
                completion_stats['recent_activity'] = {'error': 'Unable to calculate recent activity'}
            
            return completion_stats
            
        except Exception as e:
            logger.error(f"Error in _get_session_stats: {str(e)}")
            return {
                'error': 'Unable to calculate session statistics', 
                'total_teams': 0, 
                'completed_teams': 0,
                'in_progress_teams': 0,
                'completion_percentage': 0
            }
        
        return completion_stats


class SessionSubmissionsAPIView(View):
    """
    API endpoint to get all submissions for a session in WhatsApp-style format
    """
    def get(self, request, session_code):
        logger = logging.getLogger(__name__)
        
        try:
            # Import models
            from .models import TeamSubmission, DesignThinkingSession
            
            # Get session
            session = DesignThinkingSession.objects.select_related('design_game').get(
                session_code=session_code
            )
            
            # Get all submissions for this session
            submissions = TeamSubmission.objects.filter(
                team__session=session
            ).select_related('team', 'mission').order_by('submitted_at')
            
            # Format submissions for API response
            submissions_data = []
            for submission in submissions:
                submissions_data.append({
                    'id': submission.id,
                    'team': {
                        'id': submission.team.id,
                        'team_name': submission.team.team_name,
                        'team_emoji': submission.team.team_emoji
                    },
                    'mission': {
                        'id': submission.mission.id if submission.mission else None,
                        'mission_type': submission.mission.mission_type if submission.mission else 'unknown',
                        'title': submission.mission.title if submission.mission else 'Current Phase'
                    },
                    'title': submission.title,  # Submission title/label
                    'content': submission.content,  # Submission content
                    'submitted_at': submission.submitted_at.isoformat(),
                    'teacher_score': submission.teacher_score,
                    'teacher_feedback': submission.teacher_feedback or ''
                })
            
            return JsonResponse({
                'success': True,
                'submissions': submissions_data,
                'session': {
                    'session_code': session.session_code,
                    'game_title': session.design_game.title if session.design_game else 'Design Thinking'
                }
            })
            
        except DesignThinkingSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            logger.error(f"Error getting session submissions: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Server error'}, status=500)


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class ScoreSubmissionView(View):
    """
    API endpoint to score student submissions (1-10 scale)
    Simple scoring system synchronized between student and teacher sides
    """
    def post(self, request, session_code):
        logger = logging.getLogger(__name__)
        
        try:
            # Get submission data from request (handle both form data and JSON)
            if request.content_type == 'application/json' or 'application/json' in request.META.get('CONTENT_TYPE', ''):
                import json
                try:
                    raw_body = request.body
                    if isinstance(raw_body, bytes):
                        raw_body = raw_body.decode('utf-8')
                    data = json.loads(raw_body)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.error(f"JSON parsing error in scoring API: {str(e)}")
                    return JsonResponse({'error': 'Invalid JSON data'}, status=400)
                    
                submission_id = data.get('submission_id')
                score = data.get('score')
                feedback = data.get('feedback', '').strip()
            else:
                submission_id = request.POST.get('submission_id')
                score = request.POST.get('score')
                feedback = request.POST.get('feedback', '').strip()
            
            # Validate inputs
            if not submission_id:
                return JsonResponse({'error': 'Submission ID is required'}, status=400)
            
            if not score:
                return JsonResponse({'error': 'Score is required'}, status=400)
                
            try:
                score_int = int(score)
                if not (1 <= score_int <= 10):
                    return JsonResponse({'error': 'Score must be between 1 and 10'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Score must be a valid number'}, status=400)
            
            # Get the submission
            from .models import TeamSubmission, DesignThinkingSession
            
            try:
                submission = TeamSubmission.objects.select_related(
                    'team', 'mission'
                ).get(id=submission_id)
            except TeamSubmission.DoesNotExist:
                return JsonResponse({'error': 'Submission not found'}, status=404)
            
            # Verify session code matches
            if submission.team.session.session_code != session_code:
                return JsonResponse({'error': 'Session mismatch'}, status=400)
            
            # Update submission with score
            from django.utils import timezone
            submission.teacher_score = score_int  # Store as integer, not string
            submission.teacher_feedback = data.get('feedback', '')  # Optional feedback
            submission.scored_at = timezone.now()
            submission.save()
            
            logger.info(f"Scored submission {submission_id}: {score_int}/10 by teacher")
            
            # Get next unscored submission
            next_submission = TeamSubmission.objects.filter(
                team__session=submission.team.session,
                teacher_score__isnull=True
            ).select_related('team', 'mission').first()
            
            # Calculate updated progress
            total_submissions = TeamSubmission.objects.filter(
                team__session=submission.team.session
            ).count()
            scored_submissions = TeamSubmission.objects.filter(
                team__session=submission.team.session,
                teacher_score__isnull=False
            ).count()
            
            progress = {
                'scored': scored_submissions,
                'total': total_submissions,
                'percentage': round((scored_submissions / total_submissions * 100), 1) if total_submissions > 0 else 0,
                'remaining': total_submissions - scored_submissions
            }
            
            # Prepare next submission data
            next_submission_data = None
            if next_submission:
                next_submission_data = {
                    'id': next_submission.id,
                    'team_name': next_submission.team.team_name,
                    'phase_name': next_submission.mission.get_mission_type_display() if hasattr(next_submission.mission, 'get_mission_type_display') else next_submission.mission.mission_type.title(),
                    'title': next_submission.title,
                    'content': next_submission.content
                }
            
            return JsonResponse({
                'success': True,
                'message': f'Submission scored: {score_int}/10',
                'next_submission': next_submission_data,
                'progress': progress,
                'all_completed': next_submission is None
            })
            
        except Exception as e:
            logger.error(f"Error scoring submission: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': 'An error occurred while scoring the submission'
            }, status=500)



class SimplifiedInputSubmissionView(View):
    """
    Handle simplified phase input submissions via AJAX
    Processes inputs and triggers auto-progression logic
    """
    
    def post(self, request, session_code):
        try:
            # Parse JSON data
            data = json.loads(request.body)
            team_id = data.get('team_id')
            mission_id = data.get('mission_id')
            student_data = data.get('student_data', {})
            input_data = data.get('input_data', [])
            
            if not all([team_id, mission_id, input_data]):
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields: team_id, mission_id, input_data'
                })
            
            # Process input submission through auto-progression service
            from .auto_progression_service import auto_progression_service
            
            result = auto_progression_service.process_phase_input(
                team_id, mission_id, student_data, input_data
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Input submitted successfully',
                    'completion_result': result.get('completion_result'),
                    'progression_result': result.get('progression_result')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Unknown error occurred')
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data',
                'retry_allowed': False
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing simplified input submission: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Internal server error. Please try again later.',
                'retry_allowed': True,
                'debug_info': str(e) if getattr(settings, 'DEBUG', False) else None
            }, status=500)


class TeacherScoringView(View):
    """
    Handle teacher scoring submissions via AJAX
    Saves scores and broadcasts updates
    """
    
    def post(self, request, session_code):
        try:
            data = json.loads(request.body)
            team_id = data.get('team_id')
            mission_id = data.get('mission_id')
            score = data.get('score')
            teacher_id = data.get('teacher_id', f'teacher_{request.user.id if request.user.is_authenticated else "anonymous"}')
            
            if not all([team_id, mission_id, score]):
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields: team_id, mission_id, score'
                })
            
            # Save teacher score through auto-progression service
            from .auto_progression_service import auto_progression_service
            
            success = auto_progression_service.save_teacher_score(
                team_id, mission_id, score, teacher_id
            )
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': 'Score saved successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to save score'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data',
                'retry_allowed': False
            }, status=400)
        except Exception as e:
            logger.error(f"Error saving teacher score: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Failed to save score. Please try again.',
                'retry_allowed': True,
                'debug_info': str(e) if getattr(settings, 'DEBUG', False) else None
            }, status=500)


class SimplifiedFeedbackAPI(View):
    """
    Handle teacher feedback submissions and retrieval for simplified Design Thinking sessions
    """
    
    def get(self, request, session_code):
        """Get feedback for the current user's team"""
        try:
            # For now, get the first team (simplified approach)
            # In a full implementation, you'd identify the specific team
            session = get_object_or_404(DesignThinkingSession, session_code=session_code)
            teams = session.design_teams.all()
            
            if not teams:
                return JsonResponse({
                    'feedback': None,
                    'feedback_date': None,
                    'score': None
                })
            
            # Get the first team's data (simplified approach)
            team = teams.first()
            
            return JsonResponse({
                'feedback': team.teacher_feedback,
                'feedback_date': team.feedback_given_at.isoformat() if team.feedback_given_at else None,
                'score': getattr(team, 'teacher_score', None)  # Assuming score field exists
            })
            
        except Exception as e:
            logger.error(f"Error getting feedback: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': 'Failed to get feedback'
            }, status=500)
    
    def post(self, request, session_code):
        try:
            data = json.loads(request.body)
            team_id = data.get('team_id')
            feedback = data.get('feedback', '').strip()
            
            if not team_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing team_id'
                })
            
            # Get the team
            team = get_object_or_404(DesignTeam, id=team_id, session__session_code=session_code)
            
            # Update feedback
            team.teacher_feedback = feedback
            team.feedback_given_at = timezone.now() if feedback else None
            team.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Feedback saved successfully'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error saving feedback: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Failed to save feedback. Please try again.'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SimplifiedSubmissionsAPIView(View):
    """
    API endpoint to get all SimplifiedPhaseInput submissions for a session
    Used by teacher dashboard for real-time submission review
    """
    def get(self, request, session_code):
        logger = logging.getLogger(__name__)

        try:
            from .models import SimplifiedPhaseInput, DesignThinkingSession

            # Get session
            session = DesignThinkingSession.objects.select_related('design_game').get(
                session_code=session_code
            )

            # Get all simplified phase inputs for this session
            submissions = SimplifiedPhaseInput.objects.filter(
                session=session,
                is_active=True
            ).select_related('team', 'mission').order_by('submitted_at')

            # Format submissions for API response
            submissions_data = []
            for submission in submissions:
                submissions_data.append({
                    'id': submission.id,
                    'team': {
                        'id': submission.team.id,
                        'team_name': submission.team.team_name,
                        'team_emoji': submission.team.team_emoji
                    },
                    'mission': {
                        'id': submission.mission.id if submission.mission else None,
                        'mission_type': submission.mission.mission_type if submission.mission else 'unknown',
                        'title': submission.mission.title if submission.mission else 'Current Phase'
                    },
                    'student_name': submission.student_name,
                    'title': submission.input_label,  # Use input_label as title
                    'content': submission.selected_value,  # Use selected_value as content
                    'input_type': submission.input_type,
                    'submitted_at': submission.submitted_at.isoformat(),
                    'teacher_score': submission.teacher_score,
                    'scored_at': submission.scored_at.isoformat() if submission.scored_at else None
                })

            return JsonResponse({
                'success': True,
                'submissions': submissions_data,
                'session': {
                    'session_code': session.session_code,
                    'game_title': session.design_game.title if session.design_game else 'Design Thinking'
                }
            })

        except DesignThinkingSession.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)
        except Exception as e:
            logger.error(f"Error getting simplified submissions: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': 'Server error'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SimplifiedScoreSubmissionView(View):
    """
    API endpoint to score individual SimplifiedPhaseInput submissions
    Broadcasts updates via WebSocket for real-time dashboard updates
    """
    def post(self, request, session_code):
        logger = logging.getLogger(__name__)

        try:
            # Parse JSON data
            if request.content_type == 'application/json' or 'application/json' in request.META.get('CONTENT_TYPE', ''):
                try:
                    raw_body = request.body
                    if isinstance(raw_body, bytes):
                        raw_body = raw_body.decode('utf-8')
                    data = json.loads(raw_body)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.error(f"JSON parsing error: {str(e)}")
                    return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)

                submission_id = data.get('submission_id')
                score = data.get('score')
                feedback = data.get('feedback', '').strip()
            else:
                submission_id = request.POST.get('submission_id')
                score = request.POST.get('score')
                feedback = request.POST.get('feedback', '').strip()

            # Validate inputs
            if not submission_id:
                return JsonResponse({'success': False, 'error': 'Submission ID is required'}, status=400)

            if not score:
                return JsonResponse({'success': False, 'error': 'Score is required'}, status=400)

            try:
                score_int = int(score)
                if not (1 <= score_int <= 10):
                    return JsonResponse({'success': False, 'error': 'Score must be between 1 and 10'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Score must be a valid number'}, status=400)

            # Get the submission
            from .models import SimplifiedPhaseInput, DesignThinkingSession

            try:
                submission = SimplifiedPhaseInput.objects.select_related(
                    'team', 'mission', 'session'
                ).get(id=submission_id, is_active=True)
            except SimplifiedPhaseInput.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Submission not found'}, status=404)

            # Verify session code matches
            if submission.session.session_code != session_code:
                return JsonResponse({'success': False, 'error': 'Session mismatch'}, status=400)

            # Update submission with score
            submission.teacher_score = score
            submission.scored_at = timezone.now()
            submission.save()

            logger.info(f"Scored SimplifiedPhaseInput {submission_id}: {score}/10")

            # Broadcast score update via WebSocket
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                room_group_name = f'design_thinking_{session_code}'
                try:
                    async_to_sync(channel_layer.group_send)(
                        room_group_name,
                        {
                            'type': 'submission_scored_update',
                            'submission_data': {
                                'id': submission.id,
                                'team_id': submission.team.id,
                                'team_name': submission.team.team_name,
                                'team_emoji': submission.team.team_emoji,
                                'mission_title': submission.mission.title if submission.mission else '',
                                'input_label': submission.input_label,
                                'selected_value': submission.selected_value,
                                'teacher_score': score,
                                'scored_at': submission.scored_at.isoformat()
                            },
                            'timestamp': timezone.now().isoformat()
                        }
                    )
                    logger.info(f"Broadcasted score update for submission {submission_id}")
                except Exception as e:
                    logger.error(f"Error broadcasting score update: {str(e)}")

            # Get next unscored submission
            next_submission = SimplifiedPhaseInput.objects.filter(
                session=submission.session,
                teacher_score__isnull=True,
                is_active=True
            ).select_related('team', 'mission').first()

            # Calculate updated progress
            total_submissions = SimplifiedPhaseInput.objects.filter(
                session=submission.session,
                is_active=True
            ).count()
            scored_submissions = SimplifiedPhaseInput.objects.filter(
                session=submission.session,
                teacher_score__isnull=False,
                is_active=True
            ).count()

            progress = {
                'scored': scored_submissions,
                'total': total_submissions,
                'percentage': round((scored_submissions / total_submissions * 100), 1) if total_submissions > 0 else 0,
                'remaining': total_submissions - scored_submissions
            }

            # Prepare next submission data
            next_submission_data = None
            if next_submission:
                next_submission_data = {
                    'id': next_submission.id,
                    'team_name': next_submission.team.team_name,
                    'phase_name': next_submission.mission.get_mission_type_display() if next_submission.mission else 'Unknown',
                    'title': next_submission.input_label,
                    'content': next_submission.selected_value
                }

            return JsonResponse({
                'success': True,
                'message': f'Submission scored: {score}/10',
                'next_submission': next_submission_data,
                'progress': progress,
                'all_completed': next_submission is None
            })

        except Exception as e:
            logger.error(f"Error scoring simplified submission: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while scoring the submission'
            }, status=500)


class CreateSimplifiedSessionView(CreateView):
    """
    Create new simplified Design Thinking session with auto-progression
    """
    model = DesignThinkingSession
    template_name = 'group_learning/design_thinking/create_simplified_session.html'
    fields = ['school_name', 'grade_level', 'facilitator_notes']
    
    def form_valid(self, form):
        # Get or create simplified Design Thinking game
        try:
            simplified_game = DesignThinkingGame.objects.filter(
                title__icontains='Simplified',
                auto_advance_enabled=True
            ).first()
            
            if not simplified_game:
                # Create default simplified game if it doesn't exist
                from django.core.management import call_command
                call_command('setup_simplified_design_thinking')
                simplified_game = DesignThinkingGame.objects.filter(
                    auto_advance_enabled=True
                ).first()
            
            # Create session
            session = form.save(commit=False)
            session.game = simplified_game
            session.design_game = simplified_game
            session.facilitator = self.request.user if self.request.user.is_authenticated else None
            session.status = 'waiting'
            session.is_facilitator_controlled = False  # Auto-progression mode
            session.auto_advance_enabled = True
            
            # Handle optional session name from form
            session_name = self.request.POST.get('session_name', '').strip()
            if session_name:
                # Store in session_data for now (could add as a separate field later)
                session.session_data = session.session_data or {}
                session.session_data['session_name'] = session_name
            
            # Generate unique session code
            session.generate_session_code()
            session.save()
            
            messages.success(
                self.request, 
                f'Simplified Design Thinking session created: {session.session_code}'
            )
            
            return redirect('group_learning:simplified_teacher_dashboard', session_code=session.session_code)
            
        except Exception as e:
            logger.error(f"Error creating simplified session: {str(e)}", exc_info=True)
            messages.error(
                self.request,
                'Failed to create session. Please try again or contact support.'
            )
            return self.form_invalid(form)
            logger.error(f"Error creating simplified session: {str(e)}")
            form.add_error(None, f'Error creating session: {str(e)}')
            return self.form_invalid(form)
