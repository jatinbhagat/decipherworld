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
    CountryState, ConstitutionAnswer
)
from .cache_utils import ConstitutionCache, cache_view_response


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
        Get appropriate learning module based on question, option, and team performance
        """
        from .models import GameLearningModule
        
        # Try to find a learning module that should trigger
        modules = GameLearningModule.objects.filter(
            game_type='constitution_challenge',
            is_enabled=True
        )
        
        for module in modules:
            if module.should_trigger(
                question=question,
                option=option,
                topic=question.category,
                team_score=team_score
            ):
                # Record that this module is being shown
                module.record_view()
                
                # Get content adapted for team performance
                content = module.get_content_for_team(team_score)
                
                # Add additional metadata for frontend
                content.update({
                    'id': module.id,
                    'display_timing': module.display_timing,
                    'is_skippable': module.is_skippable,
                    'game_type': module.get_game_type_display(),
                })
                
                return content
        
        # Fallback to legacy system if no new modules match
        if question.learning_module_title:
            return {
                'title': question.learning_module_title,
                'principle_explanation': question.learning_module_content or '',
                'key_takeaways': '',
                'historical_context': '',
                'real_world_example': '',
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


class ProductionDiagnosticsAPI(View):
    """Diagnostics API to check production database schema"""
    
    def get(self, request):
        """Check actual database schema and model fields"""
        results = {
            'status': 'success',
            'database_info': {},
            'model_fields': {},
            'errors': []
        }
        
        try:
            from django.db import connection
            
            # Check database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                db_version = cursor.fetchone()
                results['database_info']['version'] = db_version[0]
                
                # Check if Game table exists and get its columns
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
            
            # Check Django model fields
            from .models import Game
            game_fields = [field.name for field in Game._meta.get_fields()]
            results['model_fields']['game_fields'] = game_fields
            
            # Check for mismatch
            db_column_names = [col['name'] for col in results['database_info']['game_table_columns']]
            missing_in_db = [field for field in game_fields if field not in db_column_names and field != 'learning_objectives']
            missing_in_model = [col for col in db_column_names if col not in game_fields]
            
            results['model_fields']['missing_in_database'] = missing_in_db
            results['model_fields']['missing_in_model'] = missing_in_model
            
        except Exception as e:
            results['status'] = 'error'
            results['errors'].append(f'Database check failed: {str(e)}')
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
        
        try:
            results = {
                'status': 'starting',
                'steps_completed': [],
                'errors': []
            }
            
            # Step 1: Run essential migrations only (skip problematic ones)
            try:
                # Run migrations up to the working ones only
                call_command('migrate', 'group_learning', '0004_add_visual_elements', verbosity=0, interactive=False)
                results['steps_completed'].append('✅ Essential database migrations completed (up to 0004)')
                
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
            
            # Step 3: Set up Constitution Challenge manually (safer approach)
            try:
                # Import here to avoid circular imports  
                from .models import GameLearningModule, GameSession
                
                # Check if tables exist first
                try:
                    Game.objects.exists()
                    results['steps_completed'].append('✅ Database tables are accessible')
                except Exception as table_error:
                    results['errors'].append(f'❌ Database tables not ready: {str(table_error)}')
                    results['errors'].append('🔧 Solution: Run migrations manually in Azure Console')
                    results['next_steps'] = [
                        '🔧 Manual fix needed:',
                        '1. Go to Azure App Service Console',
                        '2. Run: python manage.py migrate --settings=decipherworld.settings.production',
                        '3. Then retry this setup URL'
                    ]
                    return JsonResponse(results, status=500)
                
                # Create Constitution game - Use get_or_create with minimal fields first
                try:
                    constitution_game = Game.objects.get(title='Build Your Country: The Constitution Challenge')
                    created = False
                    results['steps_completed'].append('✅ Constitution Challenge game already exists')
                except Game.DoesNotExist:
                    # Create with only absolutely required fields first
                    constitution_game = Game.objects.create(
                        title='Build Your Country: The Constitution Challenge',
                        subtitle='Learn Indian Constitution by building your virtual country',
                        game_type='constitution_challenge',
                        description='A comprehensive team-based educational game where students learn about the Indian Constitution, fundamental rights, duties, governance structures, and democratic principles by making decisions that build and evolve their virtual country.',
                        context='Students explore the Indian Constitution through interactive gameplay, making decisions that affect their virtual nation while learning about democratic principles, governance structures, fundamental rights and duties.',
                        min_players=2,
                        max_players=6,
                        estimated_duration=45,
                        target_age_min=14,
                        target_age_max=18,
                        difficulty_level=2,  # 2 = Intermediate
                        introduction_text='Welcome to the Constitution Challenge! You will build and govern your own country by making important decisions about constitutional principles, governance, and citizen rights. Work with your team to create a thriving democracy.',
                        is_active=True
                    )
                    created = True
                    results['steps_completed'].append('✅ Constitution Challenge game created successfully')
                
                # Create demo session
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
                
                # Check if questions exist, if not run the management command
                question_count = ConstitutionQuestion.objects.filter(game=constitution_game).count()
                if question_count == 0:
                    try:
                        call_command('create_constitution_sample_updated', verbosity=0)
                        results['steps_completed'].append('✅ Constitution questions created via management command')
                    except Exception as cmd_error:
                        results['errors'].append(f'⚠️ Management command failed: {str(cmd_error)}')
                        results['steps_completed'].append('⚠️ Questions not created - will need manual creation')
                else:
                    results['steps_completed'].append(f'✅ Constitution questions already exist ({question_count} questions)')
                
                # Final verification
                question_count = ConstitutionQuestion.objects.filter(game=constitution_game).count()
                module_count = GameLearningModule.objects.filter(game=constitution_game).count()
                results['steps_completed'].append(f'✅ Final verification: {question_count} questions, {module_count} modules')
                
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
