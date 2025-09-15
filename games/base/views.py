"""
DecipherWorld Game Framework - Base Views
Hybrid architecture: Common view functionality with game-specific extensions
"""

from django.views.generic import TemplateView, DetailView, CreateView, View
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from abc import ABC, abstractmethod
import json


class BaseGameViewMixin:
    """
    Common functionality for all game views
    Provides session management, player handling, and error management
    """
    
    def get_session(self, session_code):
        """Get session with error handling"""
        try:
            return get_object_or_404(self.session_model, session_code=session_code)
        except AttributeError:
            raise NotImplementedError("session_model must be defined in subclass")
    
    def get_player(self, session, player_id=None):
        """Get current player with fallback"""
        if not hasattr(self, 'player_model'):
            raise NotImplementedError("player_model must be defined in subclass")
        
        player_id = player_id or self.request.GET.get('player_id') or self.request.session.get('player_id')
        if player_id:
            try:
                return self.player_model.objects.get(id=player_id, session=session)
            except self.player_model.DoesNotExist:
                pass
        return None
    
    def ensure_player_session(self):
        """Ensure player has a session ID"""
        if 'player_session_id' not in self.request.session:
            import uuid
            self.request.session['player_session_id'] = str(uuid.uuid4())
            self.request.session.save()
        return self.request.session['player_session_id']
    
    def add_game_message(self, message, level='info'):
        """Add user-friendly game message"""
        if level == 'error':
            messages.error(self.request, message)
        elif level == 'success':
            messages.success(self.request, message)
        else:
            messages.info(self.request, message)
    
    def get_game_context(self, session, player=None):
        """Get common game context data"""
        return {
            'session': session,
            'player': player,
            'is_game_active': session.is_active() if hasattr(session, 'is_active') else True,
            'player_count': getattr(session, 'player_count', 0),
            'session_code': session.session_code,
        }


class BaseGameSessionView(TemplateView, BaseGameViewMixin):
    """
    Base view for game session display
    Handles common session display logic
    """
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = kwargs.get('session_code')
        
        if session_code:
            session = self.get_session(session_code)
            player = self.get_player(session)
            context.update(self.get_game_context(session, player))
            
            # Add game-specific context
            if hasattr(self, 'get_game_specific_context'):
                context.update(self.get_game_specific_context(session, player))
        
        return context


class BaseGameAPIView(View, BaseGameViewMixin):
    """
    Base view for game API endpoints
    Provides consistent API response format and error handling
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Add common API setup"""
        self.ensure_player_session()
        return super().dispatch(request, *args, **kwargs)
    
    def json_response(self, data, status=200):
        """Standardized JSON response"""
        response_data = {
            'success': status < 400,
            'timestamp': timezone.now().isoformat(),
            **data
        }
        return JsonResponse(response_data, status=status)
    
    def error_response(self, message, status=400, error_code=None):
        """Standardized error response"""
        return self.json_response({
            'error': message,
            'error_code': error_code or 'GENERIC_ERROR'
        }, status=status)
    
    def handle_exception(self, exception):
        """Handle unexpected exceptions"""
        import traceback
        return self.error_response(
            'An unexpected error occurred',
            status=500,
            error_code='INTERNAL_ERROR'
        )


class BaseGameActionView(BaseGameAPIView):
    """
    Base view for processing game actions
    Handles action validation, processing, and response formatting
    """
    
    def post(self, request, session_code, *args, **kwargs):
        """Process game action"""
        try:
            session = self.get_session(session_code)
            player = self.get_player(session)
            
            if not player:
                return self.error_response('Player not found', status=404)
            
            # Validate action data
            action_data = self.get_action_data(request)
            validation_error = self.validate_action(session, player, action_data)
            if validation_error:
                return self.error_response(validation_error, status=400)
            
            # Process action
            result = self.process_game_action(session, player, action_data)
            
            # Update player activity
            if hasattr(player, 'update_activity'):
                player.update_activity()
            
            return self.json_response(result)
            
        except Exception as e:
            return self.handle_exception(e)
    
    def get_action_data(self, request):
        """Extract and parse action data from request"""
        if request.content_type == 'application/json':
            return json.loads(request.body)
        else:
            return request.POST.dict()
    
    def validate_action(self, session, player, action_data):
        """Validate action data - override in subclasses"""
        return None  # No error
    
    @abstractmethod
    def process_game_action(self, session, player, action_data):
        """Process the specific game action - must implement in subclasses"""
        pass


class GamePluginMixin:
    """
    Mixin for views that use game plugins
    Provides plugin loading and management
    """
    
    def get_game_plugin(self):
        """Get the game plugin for this view"""
        if not hasattr(self, 'game_plugin_class'):
            raise NotImplementedError("game_plugin_class must be defined")
        
        if not hasattr(self, '_game_plugin'):
            self._game_plugin = self.game_plugin_class()
        
        return self._game_plugin
    
    def get_game_config(self):
        """Get game configuration from plugin"""
        return self.get_game_plugin().get_game_config()


class SessionCreateMixin:
    """
    Mixin for creating game sessions
    Provides standardized session creation flow
    """
    
    def create_game_session(self, game_config, **kwargs):
        """Create a new game session using the configuration"""
        if not hasattr(self, 'session_model'):
            raise NotImplementedError("session_model must be defined")
        
        session_data = {
            'max_players': game_config.max_players,
            'session_data': game_config.to_dict(),
            **kwargs
        }
        
        return self.session_model.objects.create(**session_data)


class PlayerJoinMixin:
    """
    Mixin for handling player joins
    Provides standardized player creation and validation
    """
    
    def create_player(self, session, player_data):
        """Create a new player in the session"""
        if not hasattr(self, 'player_model'):
            raise NotImplementedError("player_model must be defined")
        
        # Validate player can join
        if not session.is_joinable():
            raise ValueError("Session is not joinable")
        
        # Create player
        player = self.player_model.objects.create(
            session=session,
            player_session_id=self.ensure_player_session(),
            **player_data
        )
        
        # Update session player count
        session.player_count = session.players.filter(is_active=True).count()
        session.save(update_fields=['player_count'])
        
        # Store player ID in session
        self.request.session['player_id'] = player.id
        
        return player


# Backwards Compatibility Layer

class LegacyGameViewAdapter(BaseGameSessionView):
    """
    Adapter to make legacy views work with new framework
    Ensures zero breaking changes to existing URLs
    """
    
    def get_context_data(self, **kwargs):
        # Call legacy method if it exists
        if hasattr(self, 'get_legacy_context'):
            legacy_context = self.get_legacy_context(**kwargs)
            context = super().get_context_data(**kwargs)
            context.update(legacy_context)
            return context
        
        return super().get_context_data(**kwargs)


# Development Speed Tools

class QuickGameView(BaseGameSessionView, GamePluginMixin, SessionCreateMixin, PlayerJoinMixin):
    """
    Quick setup view for simple games
    Reduces boilerplate for new game development
    """
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add quick game helpers
        context.update({
            'game_config': self.get_game_config(),
            'quick_actions': self.get_quick_actions(),
        })
        
        return context
    
    def get_quick_actions(self):
        """Get pre-built actions for rapid development"""
        return [
            {'name': 'Start Game', 'url': '#', 'class': 'btn-primary'},
            {'name': 'Join Game', 'url': '#', 'class': 'btn-secondary'},
            {'name': 'View Rules', 'url': '#', 'class': 'btn-info'},
        ]