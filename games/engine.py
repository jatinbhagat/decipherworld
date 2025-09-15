"""
DecipherWorld Game Engine
Central coordination system for all games with plugin architecture
"""

from typing import Dict, List, Type, Any, Optional
from abc import ABC, abstractmethod
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)


class GamePlugin(ABC):
    """
    Abstract base class for game plugins
    Each game type implements this interface
    """
    
    # Game identification
    game_type: str = ""
    game_name: str = ""
    game_version: str = "1.0.0"
    
    # Requirements
    requires_teams: bool = False
    min_players: int = 1
    max_players: int = 8
    
    @abstractmethod
    def get_game_config(self):
        """Return GameConfig for this game type"""
        pass
    
    @abstractmethod
    def get_session_model(self):
        """Return the Django model for game sessions"""
        pass
    
    @abstractmethod
    def get_player_model(self):
        """Return the Django model for players"""
        pass
    
    @abstractmethod
    def get_view_urls(self):
        """Return URL patterns for this game"""
        pass
    
    def get_templates_dir(self):
        """Return template directory for this game"""
        return f"games/{self.game_type}/"
    
    def get_static_dir(self):
        """Return static files directory for this game"""
        return f"games/{self.game_type}/"
    
    def validate_session_data(self, session_data: dict) -> bool:
        """Validate session creation data"""
        return True
    
    def on_session_created(self, session):
        """Hook called after session creation"""
        pass
    
    def on_player_joined(self, session, player):
        """Hook called after player joins"""
        pass
    
    def on_game_completed(self, session):
        """Hook called when game completes"""
        pass


class GamePluginRegistry:
    """
    Central registry for all game plugins
    Manages plugin discovery, registration, and retrieval
    """
    
    def __init__(self):
        self._plugins: Dict[str, GamePlugin] = {}
        self._plugin_classes: Dict[str, Type[GamePlugin]] = {}
    
    def register(self, plugin: GamePlugin):
        """Register a game plugin"""
        if not plugin.game_type:
            raise ValueError("Game plugin must have a game_type")
        
        if plugin.game_type in self._plugins:
            logger.warning(f"Overriding existing plugin for game_type: {plugin.game_type}")
        
        self._plugins[plugin.game_type] = plugin
        self._plugin_classes[plugin.game_type] = plugin.__class__
        
        logger.info(f"Registered game plugin: {plugin.game_type} - {plugin.game_name}")
    
    def get_plugin(self, game_type: str) -> Optional[GamePlugin]:
        """Get plugin by game type"""
        return self._plugins.get(game_type)
    
    def get_all_plugins(self) -> Dict[str, GamePlugin]:
        """Get all registered plugins"""
        return self._plugins.copy()
    
    def get_plugin_class(self, game_type: str) -> Optional[Type[GamePlugin]]:
        """Get plugin class by game type"""
        return self._plugin_classes.get(game_type)
    
    def autodiscover(self):
        """Automatically discover and register plugins from installed apps"""
        for app_config in apps.get_app_configs():
            self._discover_app_plugins(app_config)
    
    def _discover_app_plugins(self, app_config):
        """Discover plugins in a specific app"""
        try:
            # Try to import plugins module from the app
            module_name = f"{app_config.name}.plugins"
            module = __import__(module_name, fromlist=[''])
            
            # Look for plugin classes
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, GamePlugin) and 
                    attr != GamePlugin):
                    
                    # Instantiate and register
                    plugin_instance = attr()
                    if plugin_instance.game_type:
                        self.register(plugin_instance)
                        
        except ImportError:
            # No plugins module in this app
            pass
        except Exception as e:
            logger.error(f"Error discovering plugins in {app_config.name}: {e}")


class GameEngine:
    """
    Central game management system
    Coordinates between different game types through plugins
    """
    
    def __init__(self):
        self.registry = GamePluginRegistry()
        self._initialized = False
    
    def initialize(self):
        """Initialize the game engine"""
        if self._initialized:
            return
        
        # Auto-discover plugins
        self.registry.autodiscover()
        
        # Register built-in plugins
        self._register_builtin_plugins()
        
        self._initialized = True
        logger.info(f"Game engine initialized with {len(self.registry.get_all_plugins())} plugins")
    
    def _register_builtin_plugins(self):
        """Register built-in game plugins"""
        # This will be called during initialization
        # Plugins will register themselves via autodiscovery
        pass
    
    def get_game_types(self) -> List[str]:
        """Get all available game types"""
        self.initialize()
        return list(self.registry.get_all_plugins().keys())
    
    def get_game_info(self, game_type: str) -> Optional[dict]:
        """Get information about a specific game type"""
        self.initialize()
        plugin = self.registry.get_plugin(game_type)
        if not plugin:
            return None
        
        config = plugin.get_game_config()
        return {
            'game_type': plugin.game_type,
            'game_name': plugin.game_name,
            'game_version': plugin.game_version,
            'config': config.to_dict() if hasattr(config, 'to_dict') else config,
            'requires_teams': plugin.requires_teams,
            'player_range': f"{plugin.min_players}-{plugin.max_players}",
        }
    
    def create_session(self, game_type: str, session_data: dict = None) -> Any:
        """Create a new game session"""
        self.initialize()
        plugin = self.registry.get_plugin(game_type)
        if not plugin:
            raise ValueError(f"Unknown game type: {game_type}")
        
        # Validate session data
        session_data = session_data or {}
        if not plugin.validate_session_data(session_data):
            raise ValueError("Invalid session data")
        
        # Get the session model
        session_model = plugin.get_session_model()
        
        # Create session
        session = session_model.objects.create(**session_data)
        
        # Call plugin hook
        plugin.on_session_created(session)
        
        return session
    
    def join_session(self, game_type: str, session_code: str, player_data: dict) -> Any:
        """Add a player to a session"""
        self.initialize()
        plugin = self.registry.get_plugin(game_type)
        if not plugin:
            raise ValueError(f"Unknown game type: {game_type}")
        
        # Get models
        session_model = plugin.get_session_model()
        player_model = plugin.get_player_model()
        
        # Get session
        try:
            session = session_model.objects.get(session_code=session_code)
        except session_model.DoesNotExist:
            raise ValueError(f"Session not found: {session_code}")
        
        # Check if session is joinable
        if not session.is_joinable():
            raise ValueError("Session is not joinable")
        
        # Create player
        player = player_model.objects.create(
            session=session,
            **player_data
        )
        
        # Update session
        session.player_count = session.players.filter(is_active=True).count()
        session.save(update_fields=['player_count'])
        
        # Call plugin hook
        plugin.on_player_joined(session, player)
        
        return player
    
    def process_action(self, game_type: str, session_id: int, player_id: int, action_data: dict) -> dict:
        """Process a game action"""
        self.initialize()
        plugin = self.registry.get_plugin(game_type)
        if not plugin:
            raise ValueError(f"Unknown game type: {game_type}")
        
        # This would typically delegate to the plugin's action processor
        # For now, return a basic response
        return {
            'success': True,
            'action_processed': True,
            'game_type': game_type,
        }
    
    def get_session_state(self, game_type: str, session_id: int, player_id: int = None) -> dict:
        """Get current state of a game session"""
        self.initialize()
        plugin = self.registry.get_plugin(game_type)
        if not plugin:
            raise ValueError(f"Unknown game type: {game_type}")
        
        # This would typically delegate to the plugin
        return {
            'game_type': game_type,
            'session_id': session_id,
            'state': 'active',
        }


# Global game engine instance
game_engine = GameEngine()


# Development Tools

class GameBuilder:
    """
    Tool for rapid game development
    Provides templates and scaffolding for new games
    """
    
    @staticmethod
    def create_quiz_game(name: str, questions: List[dict]) -> dict:
        """Create a quiz-based game configuration"""
        return {
            'game_type': 'quiz',
            'name': name,
            'questions': questions,
            'scoring': 'correct_answers',
            'time_limit': 300,  # 5 minutes
        }
    
    @staticmethod
    def create_strategy_game(name: str, scenarios: List[dict]) -> dict:
        """Create a strategy/simulation game configuration"""
        return {
            'game_type': 'strategy',
            'name': name,
            'scenarios': scenarios,
            'requires_teams': True,
            'scoring': 'collaborative',
        }
    
    @staticmethod
    def create_ai_training_game(name: str, training_modules: List[dict]) -> dict:
        """Create an AI training game configuration"""
        return {
            'game_type': 'ai_training',
            'name': name,
            'modules': training_modules,
            'adaptive': True,
            'personalized': True,
        }


# Template System

class GameTemplate(ABC):
    """
    Abstract base for game templates
    Provides common structure for game types
    """
    
    @abstractmethod
    def get_base_models(self):
        """Return base models for this template"""
        pass
    
    @abstractmethod
    def get_base_views(self):
        """Return base views for this template"""
        pass
    
    @abstractmethod
    def get_base_templates(self):
        """Return base templates for this template"""
        pass


class QuizGameTemplate(GameTemplate):
    """Template for quiz-based games"""
    
    def get_base_models(self):
        return {
            'Question': 'QuestionModel',
            'Answer': 'AnswerModel',
            'Response': 'ResponseModel',
        }
    
    def get_base_views(self):
        return {
            'GameView': 'QuizGameView',
            'QuestionAPI': 'QuizQuestionAPI',
            'AnswerAPI': 'QuizAnswerAPI',
        }
    
    def get_base_templates(self):
        return {
            'game.html': 'quiz_game.html',
            'question.html': 'quiz_question.html',
            'results.html': 'quiz_results.html',
        }


class StrategyGameTemplate(GameTemplate):
    """Template for strategy/simulation games"""
    
    def get_base_models(self):
        return {
            'Scenario': 'ScenarioModel',
            'Action': 'ActionModel',
            'Team': 'TeamModel',
        }
    
    def get_base_views(self):
        return {
            'GameView': 'StrategyGameView',
            'ActionAPI': 'StrategyActionAPI',
            'TeamAPI': 'StrategyTeamAPI',
        }
    
    def get_base_templates(self):
        return {
            'game.html': 'strategy_game.html',
            'scenario.html': 'strategy_scenario.html',
            'team.html': 'strategy_team.html',
        }