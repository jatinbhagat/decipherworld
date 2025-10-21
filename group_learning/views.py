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

class DesignThinkingStartView(TemplateView):
    """Quick start page for Design Thinking sessions"""
    template_name = 'group_learning/design_thinking/quick_start.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or create the Design Thinking game
        design_game, created = DesignThinkingGame.objects.get_or_create(
            title='The Classroom Innovators Challenge',
            defaults={
                'subtitle': 'Design Thinking for Real Classroom Problems',
                'description': 'Transform your classroom environment through collaborative Design Thinking. Teams work through Empathy, Define, Ideate, and Prototype missions to solve real problems in their learning space.',
                'context': 'Students become classroom detectives and innovators, identifying problems and creating solutions for their own learning environment.',
                'game_type': 'community_building',
                'min_players': 3,
                'max_players': 30,
                'estimated_duration': 90,
                'target_age_min': 8,
                'target_age_max': 18,
                'difficulty_level': 2,
                'introduction_text': 'Welcome to the Classroom Innovators Challenge! You will work in teams to identify and solve real problems in your classroom environment using Design Thinking.',
                'is_active': True,
                'auto_advance_missions': False,
                'default_mission_duration': 15,
                'require_all_teams_complete': False,
                'enable_mentor_prompts': True,
                'mentor_prompt_frequency': 'medium'
            }
        )
        
        # Create default missions if they don't exist
        if created or not design_game.missions.exists():
            self._create_default_missions(design_game)
        
        context['game'] = design_game
        context['missions'] = design_game.missions.filter(is_active=True).order_by('order')
        
        return context
    
    def _create_default_missions(self, game):
        """Create the default 5 missions for Design Thinking"""
        missions_data = [
            {
                'mission_type': 'kickoff',
                'order': 1,
                'title': 'Energizing Kickoff',
                'description': 'Get energized and understand the challenge ahead',
                'instructions': 'Teams introduce themselves and get ready to become classroom innovators. Look around your classroom with fresh eyes!',
                'estimated_duration': 10,
                'minimum_time': 5,
                'requires_file_upload': False,
                'requires_text_submission': False,
                'max_submissions': 0,
                'learning_focus': 'Team building and problem awareness',
                'success_criteria': 'Teams are energized and ready to start observing'
            },
            {
                'mission_type': 'empathy',
                'order': 2,
                'title': 'Empathy Mission - Become Classroom Detectives',
                'description': 'Observe and document problems in your classroom environment',
                'instructions': 'Look beyond yourself. Observe how different students use the space. Take photos of problem areas. Who feels most left out? What frustrates both students and teachers?',
                'estimated_duration': 20,
                'minimum_time': 15,
                'requires_file_upload': True,
                'requires_text_submission': True,
                'max_submissions': 10,
                'learning_focus': 'Empathy, observation skills, perspective-taking',
                'success_criteria': 'Multiple observations with photos and notes about different user needs'
            },
            {
                'mission_type': 'define',
                'order': 3,
                'title': 'Define Mission - Choose Your Focus',
                'description': 'Transform observations into a specific problem statement',
                'instructions': 'Review your observations and create a Point of View statement: "A [Target User] needs to [User Need] because [Insight]"',
                'estimated_duration': 15,
                'minimum_time': 10,
                'requires_file_upload': False,
                'requires_text_submission': True,
                'max_submissions': 1,
                'learning_focus': 'Problem definition, synthesis, clear communication',
                'success_criteria': 'Clear, specific problem statement focused on a target user'
            },
            {
                'mission_type': 'ideate',
                'order': 4,
                'title': 'Ideate Mission - Brainstorm Solutions',
                'description': 'Generate as many creative solutions as possible',
                'instructions': 'Brainstorm rapidly! No idea is bad. Try "How might we..." questions. Combine crazy ideas. Go for quantity over quality!',
                'estimated_duration': 20,
                'minimum_time': 15,
                'requires_file_upload': False,
                'requires_text_submission': True,
                'max_submissions': 20,
                'learning_focus': 'Creative thinking, ideation techniques, building on ideas',
                'success_criteria': 'Many diverse ideas generated, with at least one selected for prototyping'
            },
            {
                'mission_type': 'prototype',
                'order': 5,
                'title': 'Prototype Mission - Make It Real',
                'description': 'Build a simple prototype of your best solution',
                'instructions': 'Build a quick prototype using whatever materials you have. It doesn\'t need to be perfect - just real enough to test and show others!',
                'estimated_duration': 20,
                'minimum_time': 15,
                'requires_file_upload': True,
                'requires_text_submission': True,
                'max_submissions': 3,
                'learning_focus': 'Prototyping, iteration, hands-on building',
                'success_criteria': 'Working prototype with photos and description of how it solves the problem'
            },
            {
                'mission_type': 'showcase',
                'order': 6,
                'title': 'Final Showcase - Share Your Innovation',
                'description': 'Present your solution to the class',
                'instructions': 'Share your prototype and explain how it solves the classroom problem. Get feedback and celebrate everyone\'s innovations!',
                'estimated_duration': 15,
                'minimum_time': 10,
                'requires_file_upload': False,
                'requires_text_submission': True,
                'max_submissions': 1,
                'learning_focus': 'Presentation skills, reflection, celebration of learning',
                'success_criteria': 'Clear presentation of solution with reflection on the process'
            }
        ]
        
        for mission_data in missions_data:
            DesignMission.objects.create(game=game, **mission_data)
        
        # Create default mentor nudges for each mission
        self._create_default_mentor_nudges(game)
    
    def _create_default_mentor_nudges(self, game):
        """Create default Vani mentor nudges for each mission"""
        missions = game.missions.all()
        
        nudges_data = [
            # Kickoff Mission Nudges
            {
                'mission_type': 'kickoff',
                'trigger_type': 'mission_start',
                'trigger_time_seconds': 0,
                'nudge_type': 'encouragement',
                'title': 'Welcome to Innovation!',
                'message': 'Hey innovators! 🚀 Ready to transform your classroom? Remember, every great invention started with someone noticing a problem. Let\'s begin this amazing journey together!',
                'emoji': '🚀',
                'background_color': '#10B981',
                'display_duration': 8
            },
            
            # Empathy Mission Nudges
            {
                'mission_type': 'empathy',
                'trigger_type': 'mission_start',
                'trigger_time_seconds': 0,
                'nudge_type': 'instruction',
                'title': 'Detective Mode: ON!',
                'message': 'Time to become classroom detectives! 🔍 Look beyond yourself - observe how others use this space. What problems do they face? Take photos and notes of everything you notice!',
                'emoji': '🔍',
                'background_color': '#3B82F6',
                'display_duration': 10
            },
            {
                'mission_type': 'empathy',
                'trigger_type': 'time_based',
                'trigger_time_seconds': 600,  # 10 minutes
                'nudge_type': 'prompt',
                'title': 'Dig Deeper!',
                'message': 'Great observations so far! 👀 Now think: Who feels left out in this space? What frustrates the teacher? Look for problems that aren\'t obvious at first glance.',
                'emoji': '👀',
                'background_color': '#8B5CF6',
                'display_duration': 8
            },
            
            # Define Mission Nudges
            {
                'mission_type': 'define',
                'trigger_type': 'mission_start',
                'trigger_time_seconds': 0,
                'nudge_type': 'instruction',
                'title': 'Problem Focus Time!',
                'message': 'Time to focus! 🎯 Review all your observations and pick ONE specific problem to solve. Remember: A [User] needs to [Do Something] because [Why it matters].',
                'emoji': '🎯',
                'background_color': '#F59E0B',
                'display_duration': 10
            },
            {
                'mission_type': 'define',
                'trigger_type': 'time_based',
                'trigger_time_seconds': 420,  # 7 minutes
                'nudge_type': 'prompt',
                'title': 'Be Specific!',
                'message': 'Make your problem statement super specific! 📝 Instead of "students need better classroom," try "students in the back row need better lighting because they get headaches." Specificity = Solutions!',
                'emoji': '📝',
                'background_color': '#EF4444',
                'display_duration': 8
            },
            
            # Ideate Mission Nudges
            {
                'mission_type': 'ideate',
                'trigger_type': 'mission_start',
                'trigger_time_seconds': 0,
                'nudge_type': 'encouragement',
                'title': 'Idea Storm Time!',
                'message': 'Brainstorm mode: ACTIVATED! ⚡ No idea is too crazy! Go for quantity over quality. Try to generate 10+ ideas. Build on each other\'s thoughts and let your creativity run wild!',
                'emoji': '⚡',
                'background_color': '#F59E0B',
                'display_duration': 10
            },
            {
                'mission_type': 'ideate',
                'trigger_type': 'time_based',
                'trigger_time_seconds': 300,  # 5 minutes
                'nudge_type': 'refocus',
                'title': 'No Judging Zone!',
                'message': 'Remember: NO idea is bad! 🚫❌ Don\'t judge or dismiss ideas yet. Keep generating! Try combining two different ideas together. What if you mixed idea #3 with idea #7?',
                'emoji': '🌟',
                'background_color': '#8B5CF6',
                'display_duration': 8
            },
            {
                'mission_type': 'ideate',
                'trigger_type': 'time_based',
                'trigger_time_seconds': 900,  # 15 minutes
                'nudge_type': 'celebration',
                'title': 'Ideas Flowing!',
                'message': 'Wow! Look at all those brilliant ideas! 🎉 You\'re thinking like true innovators. Now start thinking about which idea excites you most for building a prototype!',
                'emoji': '🎉',
                'background_color': '#10B981',
                'display_duration': 8
            },
            
            # Prototype Mission Nudges
            {
                'mission_type': 'prototype',
                'trigger_type': 'mission_start',
                'trigger_time_seconds': 0,
                'nudge_type': 'instruction',
                'title': 'Build Time!',
                'message': 'Time to make it real! 🔧 Pick your best idea and build a simple prototype. Use whatever materials you have - paper, cardboard, even role-playing! Make it testable!',
                'emoji': '🔧',
                'background_color': '#10B981',
                'display_duration': 10
            },
            {
                'mission_type': 'prototype',
                'trigger_type': 'time_based',
                'trigger_time_seconds': 600,  # 10 minutes
                'nudge_type': 'encouragement',
                'title': 'Progress Check!',
                'message': 'How\'s your prototype coming along? 🛠️ Remember: it doesn\'t need to be perfect! Focus on the main function. Can someone test it or see how it works? That\'s good enough!',
                'emoji': '🛠️',
                'background_color': '#F59E0B',
                'display_duration': 8
            },
            
            # Showcase Mission Nudges
            {
                'mission_type': 'showcase',
                'trigger_type': 'mission_start',
                'trigger_time_seconds': 0,
                'nudge_type': 'celebration',
                'title': 'Showcase Time!',
                'message': 'You did it! 🏆 Time to share your amazing innovation with everyone. Prepare to tell your story: the problem, your solution, and how it will help people. You should be proud!',
                'emoji': '🏆',
                'background_color': '#F59E0B',
                'display_duration': 10
            },
            {
                'mission_type': 'showcase',
                'trigger_type': 'time_based',
                'trigger_time_seconds': 420,  # 7 minutes
                'nudge_type': 'encouragement',
                'title': 'Innovation Celebration!',
                'message': 'Look at all these incredible solutions! 🌟 You\'ve learned to think like designers, builders, and problem-solvers. These skills will help you tackle any challenge in life!',
                'emoji': '🌟',
                'background_color': '#8B5CF6',
                'display_duration': 8
            }
        ]
        
        for nudge_data in nudges_data:
            mission_type = nudge_data.pop('mission_type')
            mission = missions.filter(mission_type=mission_type).first()
            if mission:
                MentorNudge.objects.create(mission=mission, **nudge_data)
    
    def post(self, request):
        """Handle session creation and team setup"""
        session_code = request.POST.get('session_code', '').strip().upper()
        team_name = request.POST.get('team_name', '').strip()
        team_emoji = request.POST.get('team_emoji', '💡')
        facilitator_mode = request.POST.get('facilitator_mode') == 'on'
        
        if not team_name:
            messages.error(request, 'Team name is required')
            return redirect('group_learning:design_thinking_start')
        
        # Get the Design Thinking game
        try:
            design_game = DesignThinkingGame.objects.get(title='The Classroom Innovators Challenge')
        except DesignThinkingGame.DoesNotExist:
            messages.error(request, 'Design Thinking game not found. Please refresh and try again.')
            return redirect('group_learning:design_thinking_start')
        
        # Handle session - either join existing or create new
        if session_code:
            try:
                session = DesignThinkingSession.objects.get(session_code=session_code)
                if session.design_game != design_game:
                    messages.error(request, 'This session code is not for the Design Thinking game')
                    return redirect('group_learning:design_thinking_start')
                
                # Check session status
                if session.status == 'completed':
                    messages.error(request, 'This session has already been completed')
                    return redirect('group_learning:design_thinking_start')
                elif session.status == 'abandoned':
                    messages.error(request, 'This session is no longer active')
                    return redirect('group_learning:design_thinking_start')
                
                # Check team limit (100 teams maximum)
                current_team_count = session.design_teams.count()
                if current_team_count >= 100:
                    messages.error(request, 'This session is full (maximum 100 teams)')
                    return redirect('group_learning:design_thinking_start')
                    
            except DesignThinkingSession.DoesNotExist:
                messages.error(request, f'Session code {session_code} not found')
                return redirect('group_learning:design_thinking_start')
        else:
            # Create new session
            session = DesignThinkingSession.objects.create(
                game=design_game,
                design_game=design_game,
                session_code=self._generate_session_code(),
                status='waiting',
                is_facilitator_controlled=True
            )
        
        # Create team
        team = DesignTeam.objects.create(
            session=session,
            team_name=team_name,
            team_emoji=team_emoji,
            team_members=[{'name': 'Team Lead', 'role': 'organizer'}]
        )
        
        # Store team info in Django session
        request.session['design_team_id'] = team.id
        request.session['design_session_code'] = session.session_code
        
        # Redirect based on mode
        if facilitator_mode:
            return redirect('group_learning:design_thinking_facilitator', session_code=session.session_code)
        else:
            return redirect('group_learning:design_thinking_play', session_code=session.session_code)
    
    def _generate_session_code(self):
        """Generate unique session code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not DesignThinkingSession.objects.filter(session_code=code).exists():
                return code


class DesignThinkingCreateView(TemplateView):
    """Teacher session creation page"""
    template_name = 'group_learning/design_thinking/create_session.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or create the Design Thinking game
        design_game, created = DesignThinkingGame.objects.get_or_create(
            title='The Classroom Innovators Challenge',
            defaults={
                'subtitle': 'Design Thinking for Real Classroom Problems',
                'description': 'Transform your classroom environment through collaborative Design Thinking. Teams work through Empathy, Define, Ideate, and Prototype missions to solve real problems in their learning space.',
                'context': 'Students become classroom detectives and innovators, identifying problems and creating solutions for their own learning environment.',
                'game_type': 'community_building',
                'min_players': 3,
                'max_players': 30,
                'estimated_duration': 90,
                'target_age_min': 8,
                'target_age_max': 18,
                'difficulty_level': 2,
                'introduction_text': 'Welcome to the Classroom Innovators Challenge! Today you will work as teams to identify real problems in your learning environment and design creative solutions.',
            }
        )
        
        context['game'] = design_game
        return context
    
    def post(self, request):
        """Handle teacher session creation"""
        facilitator_name = request.POST.get('facilitator_name', '').strip()
        session_name = request.POST.get('session_name', '').strip()
        class_info = request.POST.get('class_info', '').strip()
        auto_advance = request.POST.get('auto_advance') == 'on'
        require_all_teams = request.POST.get('require_all_teams') == 'on'
        enable_peer_viewing = request.POST.get('enable_peer_viewing') == 'on'
        
        if not facilitator_name:
            messages.error(request, 'Facilitator name is required')
            return redirect('group_learning:design_thinking_create')
        
        # Get the Design Thinking game
        try:
            design_game = DesignThinkingGame.objects.get(title='The Classroom Innovators Challenge')
        except DesignThinkingGame.DoesNotExist:
            messages.error(request, 'Design Thinking game not found. Please refresh and try again.')
            return redirect('group_learning:design_thinking_create')
        
        # Create or get facilitator user
        facilitator, created = get_user_model().objects.get_or_create(
            username=f'facilitator_{facilitator_name.lower().replace(" ", "_")}',
            defaults={
                'first_name': facilitator_name.split()[0] if facilitator_name.split() else facilitator_name,
                'last_name': ' '.join(facilitator_name.split()[1:]) if len(facilitator_name.split()) > 1 else '',
            }
        )
        
        # Create new session
        session = DesignThinkingSession.objects.create(
            game=design_game,
            design_game=design_game,
            session_code=self._generate_session_code(),
            facilitator=facilitator,
            status='waiting',
            is_facilitator_controlled=True,
            facilitator_notes=f"Session: {session_name}\nClass: {class_info}" if session_name or class_info else "",
            enable_peer_viewing=enable_peer_viewing
        )
        
        # Update game settings
        if auto_advance:
            design_game.auto_advance_missions = True
            design_game.save()
        if require_all_teams:
            design_game.require_all_teams_complete = True
            design_game.save()
        
        # Set first mission
        first_mission = DesignMission.objects.filter(game=design_game).order_by('order').first()
        if first_mission:
            session.current_mission = first_mission
            session.save()
        
        # Store session info for facilitator
        request.session['facilitator_session_code'] = session.session_code
        request.session['is_facilitator'] = True
        
        messages.success(request, f'Session created successfully! Share code "{session.session_code}" with your students.')
        return redirect('group_learning:design_thinking_facilitator', session_code=session.session_code)
    
    def _generate_session_code(self):
        """Generate unique session code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not DesignThinkingSession.objects.filter(session_code=code).exists():
                return code


class DesignThinkingJoinView(TemplateView):
    """Student session joining page"""
    template_name = 'group_learning/design_thinking/join_session.html'
    
    def post(self, request):
        """Handle student session joining"""
        session_code = request.POST.get('session_code', '').strip().upper()
        team_name = request.POST.get('team_name', '').strip()
        team_emoji = request.POST.get('team_emoji', '💡')
        team_members = request.POST.get('team_members', '').strip()
        
        if not session_code:
            messages.error(request, 'Session code is required')
            return redirect('group_learning:design_thinking_join')
            
        if not team_name:
            messages.error(request, 'Team name is required')
            return redirect('group_learning:design_thinking_join')
        
        # Get the Design Thinking game
        try:
            design_game = DesignThinkingGame.objects.get(title='The Classroom Innovators Challenge')
        except DesignThinkingGame.DoesNotExist:
            messages.error(request, 'Design Thinking game not found. Please refresh and try again.')
            return redirect('group_learning:design_thinking_join')
        
        # Find and validate session
        try:
            session = DesignThinkingSession.objects.get(session_code=session_code)
            if session.design_game != design_game:
                messages.error(request, 'This session code is not for the Design Thinking game')
                return redirect('group_learning:design_thinking_join')
            
            # Check session status
            if session.status == 'completed':
                messages.error(request, 'This session has already been completed')
                return redirect('group_learning:design_thinking_join')
            elif session.status == 'abandoned':
                messages.error(request, 'This session is no longer active')
                return redirect('group_learning:design_thinking_join')
            
            # Check team limit (100 teams maximum)
            current_team_count = session.design_teams.count()
            if current_team_count >= 100:
                messages.error(request, 'This session is full (maximum 100 teams)')
                return redirect('group_learning:design_thinking_join')
                
        except DesignThinkingSession.DoesNotExist:
            messages.error(request, f'Session code {session_code} not found')
            return redirect('group_learning:design_thinking_join')
        
        # Parse team members
        team_members_list = []
        if team_members:
            members = [m.strip() for m in team_members.split(',') if m.strip()]
            team_members_list = [{'name': name, 'role': 'member'} for name in members]
        
        # Check for duplicate team name in session
        if DesignTeam.objects.filter(session=session, team_name=team_name).exists():
            messages.error(request, f'Team name "{team_name}" is already taken in this session. Please choose a different name.')
            return redirect('group_learning:design_thinking_join')
        
        # Create team
        team = DesignTeam.objects.create(
            session=session,
            team_name=team_name,
            team_emoji=team_emoji,
            team_members=team_members_list
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
        return redirect('group_learning:design_thinking_play', session_code=session.session_code)
    
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
                'members': team.team_members
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


class DesignThinkingFacilitatorView(TemplateView):
    """Mission Control Dashboard for facilitators"""
    template_name = 'group_learning/design_thinking/facilitator_dashboard.html'
    
    def get(self, request, *args, **kwargs):
        session_code = kwargs['session_code']
        
        try:
            session = DesignThinkingSession.objects.select_related('design_game').get(session_code=session_code)
        except DesignThinkingSession.DoesNotExist:
            messages.error(request, 'Session not found')
            return redirect('group_learning:design_thinking_start')
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs['session_code']
        
        session = DesignThinkingSession.objects.select_related('design_game').get(session_code=session_code)
        
        context['session'] = session
        context['game'] = session.design_game
        context['missions'] = session.design_game.missions.filter(is_active=True).order_by('order')
        
        # Get detailed team data with progress information
        teams_with_progress = []
        for team in session.design_teams.all().order_by('team_name'):
            # Get mission-specific progress for this team
            empathy_observations_count = 0
            current_mission_submissions = 0
            mission_completed = False
            
            if session.current_mission:
                # Get current mission progress
                try:
                    current_progress = TeamProgress.objects.get(
                        session=session,
                        team=team,
                        mission=session.current_mission
                    )
                    mission_completed = current_progress.is_completed
                    current_mission_submissions = current_progress.submission_count
                except TeamProgress.DoesNotExist:
                    # Create missing progress record
                    current_progress = TeamProgress.objects.create(
                        session=session,
                        team=team,
                        mission=session.current_mission
                    )
                
                # Get empathy-specific data
                if session.current_mission.mission_type == 'empathy':
                    empathy_observations_count = team.submissions.filter(
                        mission=session.current_mission,
                        submission_type='empathy_observation'
                    ).count()
            
            # Add computed fields to team object
            team.empathy_observations_count = empathy_observations_count
            team.current_mission_submissions = current_mission_submissions
            team.mission_completed = mission_completed
            team.actual_progress_percentage = team.get_progress_percentage()
            
            teams_with_progress.append(team)
        
        context['teams'] = teams_with_progress
        context['current_mission'] = session.current_mission
        
        # Get next mission for UI
        if session.current_mission:
            next_mission = session.design_game.missions.filter(
                is_active=True,
                order__gt=session.current_mission.order
            ).order_by('order').first()
            context['next_mission'] = next_mission
        else:
            # If no current mission, next is the first mission
            context['next_mission'] = session.design_game.missions.filter(is_active=True).order_by('order').first()
        
        # Get mission progress
        context['mission_progress'] = session.get_mission_progress()
        
        # Get recent submissions
        context['recent_submissions'] = TeamSubmission.objects.filter(
            team__session=session
        ).select_related('team', 'mission').order_by('-submitted_at')[:10]
        
        return context


class DesignThinkingPlayView(TemplateView):
    """Student team interface for playing the game"""
    template_name = 'group_learning/design_thinking/team_interface.html'
    
    def dispatch(self, request, *args, **kwargs):
        team_id = request.session.get('design_team_id')
        session_code = kwargs['session_code']
        
        if not team_id:
            messages.error(request, 'Please join a team first')
            return redirect('group_learning:design_thinking_start')
        
        try:
            session = DesignThinkingSession.objects.select_related('design_game').get(session_code=session_code)
            team = DesignTeam.objects.get(id=team_id, session=session)
        except (DesignThinkingSession.DoesNotExist, DesignTeam.DoesNotExist):
            messages.error(request, 'Session or team not found')
            return redirect('group_learning:design_thinking_start')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs['session_code']
        team_id = self.request.session.get('design_team_id')
        
        # Check if specific mission is requested via URL parameter
        requested_mission_type = self.request.GET.get('mission')
        
        # These should exist because dispatch already validated them, but add safety check
        try:
            session = DesignThinkingSession.objects.select_related('design_game').get(session_code=session_code)
            team = DesignTeam.objects.get(id=team_id, session=session)
        except (DesignThinkingSession.DoesNotExist, DesignTeam.DoesNotExist):
            # This should not happen if dispatch worked correctly, but handle gracefully
            context['error'] = 'Session or team data not available'
            return context
        
        # Handle mission navigation - allow teams to view missions they've earned access to
        display_mission = session.current_mission  # Default to session's current mission
        
        if requested_mission_type and session.current_mission:
            # Find the requested mission
            requested_mission = session.design_game.missions.filter(
                is_active=True,
                mission_type=requested_mission_type
            ).first()
            
            if requested_mission:
                # Check if team has earned access to this mission
                can_access = False
                
                if requested_mission.order <= session.current_mission.order:
                    # Mission is current or earlier - always accessible
                    can_access = True
                else:
                    # Mission is ahead - check if team completed all previous missions
                    previous_missions = session.design_game.missions.filter(
                        is_active=True,
                        order__lt=requested_mission.order
                    ).order_by('order')
                    
                    all_completed = True
                    for prev_mission in previous_missions:
                        try:
                            progress = TeamProgress.objects.get(
                                session=session,
                                team=team,
                                mission=prev_mission
                            )
                            if not progress.is_completed:
                                all_completed = False
                                break
                        except TeamProgress.DoesNotExist:
                            all_completed = False
                            break
                    
                    can_access = all_completed
                
                if can_access:
                    display_mission = requested_mission
                    context['mission_navigation'] = {
                        'navigated_to': requested_mission.mission_type,
                        'message': f'Viewing {requested_mission.title}'
                    }
                else:
                    context['mission_navigation'] = {
                        'navigated_to': None,
                        'message': 'Complete previous missions to access this one'
                    }
        
        context['session'] = session
        context['team'] = team
        context['game'] = session.design_game
        context['current_mission'] = display_mission  # Use the display mission (may be different from session's current)
        context['session_current_mission'] = session.current_mission  # Keep original for reference
        context['missions'] = session.design_game.missions.filter(is_active=True).order_by('order')
        
        # Get team's submissions for the mission being displayed
        if display_mission:
            context['team_submissions'] = team.submissions.filter(
                mission=display_mission
            ).order_by('-submitted_at')
        else:
            context['team_submissions'] = []
        
        # Calculate actual team progress based on completed missions, not current position
        completed_missions_count = 0
        current_mission_position = 0
        
        if session.current_mission:
            # Get all missions ordered by sequence
            all_missions = list(session.design_game.missions.filter(is_active=True).order_by('order'))
            
            # Count actually completed missions for this team
            completed_missions_count = team.mission_progress.filter(
                is_completed=True,
                mission__in=all_missions
            ).count()
            
            # Get current mission position (1-based) for display purposes
            try:
                current_mission_position = next(i for i, mission in enumerate(all_missions) 
                                              if mission.id == session.current_mission.id) + 1
            except StopIteration:
                current_mission_position = 1
        
        # team_progress now represents actual completed missions, not current position
        context['team_progress'] = completed_missions_count
        context['current_mission_position'] = current_mission_position
        context['total_missions'] = session.design_game.missions.filter(is_active=True).count()
        
        # Add mission position to each mission for template use
        all_missions = list(session.design_game.missions.filter(is_active=True).order_by('order'))
        for i, mission in enumerate(all_missions):
            mission.position = i + 1  # 1-based position (1-6)
        context['missions'] = all_missions
        
        return context


class DesignThinkingSubmissionAPI(View):
    """API for team submissions during missions"""
    
    def post(self, request, session_code):
        import logging
        logger = logging.getLogger(__name__)
        
        # Enhanced debugging for submission issues
        team_id = request.session.get('design_team_id')
        logger.info(f"Submission API called for session {session_code}, team_id: {team_id}")
        
        if not team_id:
            logger.warning(f"No team_id in session for {session_code}")
            return JsonResponse({'error': 'Team not found in session', 'debug': 'No design_team_id in session'}, status=400)
        
        try:
            session = DesignThinkingSession.objects.get(session_code=session_code)
            team = DesignTeam.objects.get(id=team_id, session=session)
            logger.info(f"Found team {team.team_name} (ID: {team.id}) in session {session_code}")
        except DesignThinkingSession.DoesNotExist:
            logger.error(f"Session {session_code} not found")
            return JsonResponse({'error': 'Session not found'}, status=404)
        except DesignTeam.DoesNotExist:
            logger.error(f"Team {team_id} not found in session {session_code}")
            return JsonResponse({'error': 'Team not found in session'}, status=404)
        
        if not session.current_mission:
            logger.warning(f"No active mission for session {session_code}")
            return JsonResponse({'error': 'No active mission'}, status=400)
        
        # Get submission data
        submission_type = request.POST.get('submission_type')
        content = request.POST.get('content', '')
        title = request.POST.get('title', '')
        submitted_by = request.POST.get('submitted_by', 'Anonymous')
        
        logger.info(f"Creating submission: type={submission_type}, content_length={len(content)}")
        
        # Handle file upload
        uploaded_file = request.FILES.get('file')
        file_type = None  # Default to None for text-only submissions
        if uploaded_file:
            if uploaded_file.content_type.startswith('image/'):
                file_type = 'image'
            elif uploaded_file.content_type.startswith('audio/'):
                file_type = 'audio'
            else:
                file_type = 'document'
        
        try:
            # Create submission using centralized service
            submission = SubmissionService.create_submission(
                team=team,
                mission=session.current_mission,
                submission_type=submission_type,
                content=content,
                title=title,
                uploaded_file=uploaded_file
            )
            logger.info(f"Successfully created submission {submission.id} for team {team.team_name}")
        except Exception as e:
            logger.error(f"Failed to create submission: {e}")
            return JsonResponse({'error': f'Failed to create submission: {str(e)}'}, status=500)
        
        # Update team submission count
        team.total_submissions += 1
        team.save()
        
        # Check if mission should be marked complete for this team
        progress, created = TeamProgress.objects.get_or_create(
            session=session,
            team=team,
            mission=session.current_mission
        )
        if created:
            logger.info(f"Created new TeamProgress for team {team.team_name}, mission {session.current_mission.title}")
        
        progress.submission_count += 1
        
        # Specific logic for empathy mission - check observation count
        if session.current_mission.mission_type == 'empathy':
            empathy_observations = team.submissions.filter(
                mission=session.current_mission, 
                submission_type='empathy_observation'
            ).count()
            logger.info(f"Team {team.team_name} has {empathy_observations} empathy observations")
            
            # Mark empathy mission complete if team has 5+ observations
            if empathy_observations >= 5 and not progress.is_completed:
                progress.mark_completed()
                logger.info(f"Empathy mission completed for team {team.team_name} with {empathy_observations} observations")
            else:
                progress.save()
        else:
            # General mission completion logic for other missions
            if (not session.current_mission.requires_text_submission or 
                team.submissions.filter(mission=session.current_mission, content__isnull=False).exists()) and \
               (not session.current_mission.requires_file_upload or 
                team.submissions.filter(mission=session.current_mission, uploaded_file__isnull=False).exists()):
                progress.mark_completed()
            else:
                progress.save()
        
        # Broadcast team submission via WebSocket
        self._broadcast_team_submission(session.session_code, team, submission)
        
        # Calculate current mission progress for response
        current_mission_submissions = team.submissions.filter(mission=session.current_mission).count()
        empathy_observations = team.submissions.filter(
            mission=session.current_mission, 
            submission_type='empathy_observation'
        ).count() if session.current_mission.mission_type == 'empathy' else 0
        
        response_data = {
            'success': True,
            'submission_id': submission.id,
            'team_submissions_count': current_mission_submissions,
            'mission_completed': progress.is_completed,
            'empathy_observations_count': empathy_observations,
            'can_advance': progress.is_completed,
            'mission_type': session.current_mission.mission_type,
            'debug_info': {
                'team_id': team.id,
                'session_code': session_code,
                'mission_title': session.current_mission.title
            }
        }
        
        logger.info(f"Submission response: {response_data}")
        return JsonResponse(response_data)


class DesignThinkingMissionControlAPI(View):
    """API for facilitator mission control - uses centralized DesignThinkingService"""
    
    def post(self, request, session_code):
        action = request.POST.get('action')
        
        try:
            session = DesignThinkingSession.objects.select_related('design_game').get(session_code=session_code)
        except DesignThinkingSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        
        # Initialize service for this session
        service = DesignThinkingService(session)
        
        if action == 'advance_mission':
            mission_order = request.POST.get('mission_order')
            
            if not mission_order:
                # If no specific order provided, advance to next mission
                try:
                    result = service.advance_to_next_mission()
                    return JsonResponse(result)
                except MissionAdvancementError as e:
                    return JsonResponse({'error': str(e)}, status=400)
            else:
                # Advance to specific mission order
                try:
                    mission_order = int(mission_order)
                    result = service.advance_to_mission(mission_order)
                    return JsonResponse(result)
                except (ValueError, MissionAdvancementError) as e:
                    return JsonResponse({'error': str(e)}, status=400)
        
        elif action == 'start_session':
            # Start session with first mission (Kickoff)
            try:
                result = service.advance_to_mission(1)  # Start with Kickoff mission
                return JsonResponse({
                    'success': True,
                    'status': 'started',
                    'message': 'Session started successfully!',
                    **result
                })
            except MissionAdvancementError as e:
                return JsonResponse({'error': str(e)}, status=400)
        
        elif action == 'end_session':
            # Use the new complete_session method
            session.complete_session()
            
            # Broadcast session completion via WebSocket
            self._broadcast_session_completed(session_code)
            
            return JsonResponse({
                'success': True,
                'status': 'completed',
                'message': 'Session completed successfully!'
            })
        
        elif action == 'complete_showcase':
            # Complete the final showcase mission and end session
            if session.is_final_mission():
                session.complete_session()
                
                # Broadcast session completion
                self._broadcast_session_completed(session_code)
                
                return JsonResponse({
                    'success': True,
                    'status': 'completed',
                    'message': 'Showcase completed! Session ended successfully!'
                })
            else:
                return JsonResponse({'error': 'Not in final mission'}, status=400)
        
        elif action == 'get_progress':
            # Get comprehensive session progress
            try:
                progress_data = service.get_session_progress()
                return JsonResponse({
                    'success': True,
                    'progress': progress_data
                })
            except Exception as e:
                return JsonResponse({'error': f'Failed to get progress: {str(e)}'}, status=500)
        
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    def _broadcast_team_submission(self, session_code, team, submission):
        """Broadcast team submission to all connected clients"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f'design_thinking_{session_code}'
            team_data = {
                'id': team.id,
                'name': team.team_name,
                'emoji': team.team_emoji,
                'color': team.team_color
            }
            submission_data = {
                'id': submission.id,
                'type': submission.submission_type,
                'title': submission.title,
                'content': submission.content[:100] + '...' if len(submission.content) > 100 else submission.content,
                'submitted_by': submission.submitted_by,
                'has_file': bool(submission.uploaded_file)
            }
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'team_submission_update',
                    'team_data': team_data,
                    'submission_data': submission_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    def _broadcast_mission_advanced(self, session_code, mission):
        """Broadcast mission advancement to all connected clients"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f'design_thinking_{session_code}'
            message_data = {
                'id': mission.id,
                'title': mission.title,
                'mission_type': mission.mission_type,
                'description': mission.description,
                'instructions': mission.instructions
            }
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'mission_advanced',
                    'mission_data': message_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    def _broadcast_session_completed(self, session_code):
        """Broadcast session completion to all connected clients"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f'design_thinking_{session_code}'
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'session_completed',
                    'message': 'Session has been completed!',
                    'timestamp': timezone.now().isoformat()
                }
            )


class DesignThinkingStatusAPI(View):
    """API for real-time session status updates"""
    
    def get(self, request, session_code):
        try:
            session = DesignThinkingSession.objects.select_related('current_mission').get(session_code=session_code)
        except DesignThinkingSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        
        # Get team-specific data if team_id is in session
        team_id = request.session.get('design_team_id')
        team_specific_data = {}
        
        if team_id:
            try:
                team = DesignTeam.objects.get(id=team_id, session=session)
                
                # Get team progress for current mission
                current_mission_progress = None
                if session.current_mission:
                    progress, created = TeamProgress.objects.get_or_create(
                        session=session,
                        team=team,
                        mission=session.current_mission
                    )
                    
                    # Get empathy observations count
                    empathy_observations_count = 0
                    if session.current_mission.mission_type == 'empathy':
                        empathy_observations_count = team.submissions.filter(
                            mission=session.current_mission,
                            submission_type='empathy_observation'
                        ).count()
                    
                    team_specific_data = {
                        'team_id': team.id,
                        'team_name': team.team_name,
                        'mission_completed': progress.is_completed,
                        'can_advance': progress.is_completed,
                        'empathy_observations_count': empathy_observations_count,
                        'current_mission_submissions': team.submissions.filter(mission=session.current_mission).count()
                    }
            except DesignTeam.DoesNotExist:
                pass
        
        # Get teams and their detailed progress data
        teams_data = []
        for team in session.design_teams.all():
            # Get mission-specific progress
            mission_progress_data = {}
            empathy_observations_count = 0
            current_mission_submissions = 0
            
            if session.current_mission:
                # Get current mission progress
                try:
                    current_progress = TeamProgress.objects.get(
                        session=session,
                        team=team,
                        mission=session.current_mission
                    )
                    mission_progress_data = {
                        'is_completed': current_progress.is_completed,
                        'submission_count': current_progress.submission_count,
                        'started_at': current_progress.started_at.isoformat() if current_progress.started_at else None,
                        'completed_at': current_progress.completed_at.isoformat() if current_progress.completed_at else None
                    }
                except TeamProgress.DoesNotExist:
                    mission_progress_data = {
                        'is_completed': False,
                        'submission_count': 0,
                        'started_at': None,
                        'completed_at': None
                    }
                
                # Get empathy-specific data
                if session.current_mission.mission_type == 'empathy':
                    empathy_observations_count = team.submissions.filter(
                        mission=session.current_mission,
                        submission_type='empathy_observation'
                    ).count()
                
                # Get current mission submissions
                current_mission_submissions = team.submissions.filter(
                    mission=session.current_mission
                ).count()
            
            teams_data.append({
                'id': team.id,
                'name': team.team_name,
                'emoji': team.team_emoji,
                'color': team.team_color,
                'missions_completed': team.mission_progress.filter(is_completed=True).count(),
                'total_submissions': team.total_submissions,
                'progress_percentage': team.get_progress_percentage(),
                'current_mission_progress': mission_progress_data,
                'empathy_observations_count': empathy_observations_count,
                'current_mission_submissions': current_mission_submissions,
                'created_at': team.created_at.isoformat() if hasattr(team, 'created_at') else None
            })
        
        # Get active Vani nudges for current mission
        active_nudges = []
        if session.current_mission and session.mission_start_time:
            from django.utils import timezone
            mission_elapsed_seconds = (timezone.now() - session.mission_start_time).total_seconds()
            
            # Get nudges that should be triggered
            nudges = session.current_mission.mentor_nudges.filter(
                is_active=True,
                trigger_time_seconds__lte=mission_elapsed_seconds
            ).order_by('trigger_time_seconds')
            
            for nudge in nudges:
                active_nudges.append({
                    'id': nudge.id,
                    'title': nudge.title,
                    'message': nudge.message,
                    'emoji': nudge.emoji,
                    'background_color': nudge.background_color,
                    'nudge_type': nudge.nudge_type,
                    'display_duration': nudge.display_duration,
                    'is_dismissible': nudge.is_dismissible
                })

        response_data = {
            'success': True,
            'status': session.status,
            'current_mission': session.current_mission.mission_type if session.current_mission else None,
            'current_mission_details': {
                'id': session.current_mission.id,
                'title': session.current_mission.title,
                'mission_type': session.current_mission.mission_type,
                'description': session.current_mission.description
            } if session.current_mission else None,
            'teams': teams_data,
            'teams_count': len(teams_data),
            'mission_progress': session.get_mission_progress(),
            'session_started': session.started_at.isoformat() if session.started_at else None,
            'mission_started': session.mission_start_time.isoformat() if session.mission_start_time else None,
            'active_nudges': active_nudges
        }
        
        # Add team-specific data if available
        response_data.update(team_specific_data)
        
        return JsonResponse(response_data)


class DesignThinkingMissionInterfaceAPI(View):
    """API endpoint to get just the mission interface HTML for dynamic updates"""
    
    def get(self, request, session_code):
        try:
            # Get session
            session = DesignThinkingSession.objects.select_related('design_game').get(
                session_code=session_code
            )
            
            # Get team from session
            team_id = request.session.get('design_team_id')
            if not team_id:
                return HttpResponseBadRequest('No team session found')
            
            try:
                team = DesignTeam.objects.get(id=team_id, session=session)
            except DesignTeam.DoesNotExist:
                return HttpResponseBadRequest('Team not found in this session')
            
            # Get current mission and team data (same logic as DesignThinkingPlayView)
            current_mission = session.current_mission
            
            if not current_mission:
                # Return waiting state HTML
                html_content = '''
                <div class="card p-8 text-center mb-6">
                    <div class="text-6xl mb-4">⏳</div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-4">Ready to Start!</h2>
                    <p class="text-lg text-gray-600 mb-6">
                        Your team is ready. Waiting for your teacher to begin the challenge.
                    </p>
                    <div class="inline-flex items-center px-4 py-2 bg-yellow-100 text-yellow-800 rounded-lg">
                        <span class="w-2 h-2 rounded-full bg-yellow-500 mr-2"></span>
                        <span>Waiting for teacher</span>
                    </div>
                </div>
                '''
                return HttpResponse(html_content)
            
            # Prepare context for mission interface template
            context = {
                'session': session,
                'team': team,
                'current_mission': current_mission,
                'team_submissions': team.submissions.filter(mission=current_mission).order_by('-submitted_at')[:10],
                'team_progress': TeamProgress.objects.filter(session=session, team=team).count(),
                'total_missions': session.design_game.missions.filter(is_active=True).count(),
            }
            
            # Render the mission interface template based on mission type
            mission_template_map = {
                'kickoff': 'group_learning/design_thinking/missions/kickoff.html',
                'empathy': 'group_learning/design_thinking/missions/empathy.html',
                'define': 'group_learning/design_thinking/missions/define.html',
                'ideate': 'group_learning/design_thinking/missions/ideate.html',
                'prototype': 'group_learning/design_thinking/missions/prototype.html',
                'showcase': 'group_learning/design_thinking/missions/showcase.html',
            }
            
            mission_template = mission_template_map.get(current_mission.mission_type)
            
            if mission_template:
                # Render the specific mission template
                from django.template.loader import render_to_string
                html_content = render_to_string(mission_template, context, request=request)
            else:
                # Fallback to basic mission display
                html_content = f'''
                <div class="card p-6 mb-6">
                    <div class="flex items-start space-x-4 mb-6">
                        <div class="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center text-white text-xl font-bold">
                            📋
                        </div>
                        <div class="flex-1">
                            <h2 class="text-2xl font-bold text-gray-800 mb-2">{current_mission.title}</h2>
                            <p class="text-gray-600 mb-3">{current_mission.description}</p>
                            <div class="flex items-center space-x-4">
                                <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                                    Active Mission
                                </span>
                                <span class="text-sm text-gray-500">
                                    📅 {current_mission.estimated_duration} minutes
                                </span>
                            </div>
                        </div>
                    </div>
                    {f'<div class="bg-blue-50 rounded-lg p-4 mb-6"><h3 class="font-bold text-gray-800 mb-2">🎯 Your Mission</h3><p class="text-gray-700">{current_mission.instructions}</p></div>' if current_mission.instructions else ''}
                </div>
                '''
            
            return HttpResponse(html_content)
            
        except DesignThinkingSession.DoesNotExist:
            return HttpResponseBadRequest('Session not found')
        except Exception as e:
            logger.error(f"Mission interface API error: {str(e)}")
            return HttpResponseBadRequest(f'Error loading mission interface: {str(e)}')
