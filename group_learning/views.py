from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, TemplateView, View
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from django.forms import ModelForm, CharField, ChoiceField
from django.core.exceptions import ValidationError
import random
import string
import json

from .models import (
    Game, GameSession, Role, Scenario, Action, Outcome, 
    PlayerAction, ReflectionResponse, LearningObjective
)


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
    queryset = Game.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.get_object()
        context['scenarios'] = game.scenarios.filter(is_active=True).order_by('order')
        context['roles'] = Role.objects.filter(is_active=True, scenarios__game=game).distinct()
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
                    scenarios__game=self.session.game,
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
                scenarios__game=session.game,
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs['session_code']
        session = get_object_or_404(GameSession, session_code=session_code)
        
        # Check if player is in session
        player_session_id = self.request.session.get('player_session_id')
        if not player_session_id:
            messages.error(self.request, 'You must join the session first.')
            return redirect('group_learning:session_detail', session_code=session_code)
        
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
            )
            context['available_actions'] = available_actions
        
        # Get previous actions by this player
        context['player_actions'] = PlayerAction.objects.filter(
            session=session,
            player_session_id=player_session_id
        ).order_by('-decision_time')
        
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
                scenarios__game=session.game,
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
        
        role_played = player_action.role if player_action else None
        
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
        session = get_object_or_404(GameSession, session_code=session_code)
        
        # Get player count
        players = session.player_actions.values('player_name', 'player_session_id').distinct()
        
        return JsonResponse({
            'status': session.status,
            'player_count': len(players),
            'current_scenario': session.current_scenario.title if session.current_scenario else None,
            'game_title': session.game.title
        })


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
