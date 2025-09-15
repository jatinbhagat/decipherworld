"""
DecipherWorld Game Development Speed Tools
Rapid game creation and scaffolding utilities
"""

import os
from typing import Dict, List, Any, Optional
from django.template import Template, Context
from django.core.management.base import BaseCommand
from django.apps import apps


class GameScaffold:
    """
    Scaffolding tool for creating new games quickly
    Generates models, views, templates, and URLs
    """
    
    def __init__(self, game_name: str, game_type: str, app_name: str = None):
        self.game_name = game_name
        self.game_type = game_type
        self.app_name = app_name or f"{game_type}_game"
        self.base_path = f"games/{self.game_type}"
    
    def create_game_structure(self):
        """Create complete game structure"""
        structure = {
            'models': self.generate_models(),
            'views': self.generate_views(),
            'urls': self.generate_urls(),
            'templates': self.generate_templates(),
            'plugin': self.generate_plugin(),
            'admin': self.generate_admin(),
        }
        
        return structure
    
    def generate_models(self) -> str:
        """Generate models.py content"""
        template = Template("""
from django.db import models
from games.base.models import BaseGameSession, BaseGamePlayer

class {{ game_class }}Session(BaseGameSession):
    \"\"\"Game session for {{ game_name }}\"\"\"
    
    # Game-specific fields
    game_settings = models.JSONField(default=dict)
    current_stage = models.CharField(max_length=50, default='setup')
    
    class Meta:
        db_table = '{{ app_name }}_session'
        indexes = [
            models.Index(fields=['session_code', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def get_absolute_url(self):
        return f"/{{ game_type }}/{self.session_code}/"

class {{ game_class }}Player(BaseGamePlayer):
    \"\"\"Player for {{ game_name }}\"\"\"
    
    session = models.ForeignKey({{ game_class }}Session, on_delete=models.CASCADE, related_name='players')
    
    # Game-specific fields
    game_progress = models.JSONField(default=dict)
    current_level = models.PositiveIntegerField(default=1)
    
    class Meta:
        db_table = '{{ app_name }}_player'
        unique_together = ['session', 'player_session_id']
        indexes = [
            models.Index(fields=['session', 'is_active']),
            models.Index(fields=['last_activity']),
        ]

class {{ game_class }}Action(models.Model):
    \"\"\"Actions taken in {{ game_name }}\"\"\"
    
    player = models.ForeignKey({{ game_class }}Player, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=50)
    action_data = models.JSONField(default=dict)
    points_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = '{{ app_name }}_action'
        indexes = [
            models.Index(fields=['player', 'created_at']),
            models.Index(fields=['action_type']),
        ]
""")
        
        context = Context({
            'game_name': self.game_name,
            'game_type': self.game_type,
            'game_class': self._to_class_name(self.game_name),
            'app_name': self.app_name,
        })
        
        return template.render(context)
    
    def generate_views(self) -> str:
        """Generate views.py content"""
        template = Template("""
from django.shortcuts import get_object_or_404
from games.base.views import BaseGameSessionView, BaseGameActionView, QuickGameView
from .models import {{ game_class }}Session, {{ game_class }}Player
from .plugins import {{ game_class }}Plugin

class {{ game_class }}GameView(QuickGameView):
    \"\"\"Main game view for {{ game_name }}\"\"\"
    
    template_name = '{{ game_type }}/game.html'
    session_model = {{ game_class }}Session
    player_model = {{ game_class }}Player
    game_plugin_class = {{ game_class }}Plugin
    
    def get_game_specific_context(self, session, player):
        \"\"\"Add game-specific context data\"\"\"
        return {
            'game_name': '{{ game_name }}',
            'current_stage': session.current_stage if session else 'setup',
            'player_progress': player.game_progress if player else {},
        }

class {{ game_class }}ActionAPI(BaseGameActionView):
    \"\"\"API for processing {{ game_name }} actions\"\"\"
    
    session_model = {{ game_class }}Session
    player_model = {{ game_class }}Player
    
    def process_game_action(self, session, player, action_data):
        \"\"\"Process specific action for {{ game_name }}\"\"\"
        
        action_type = action_data.get('action_type')
        
        # Example action processing
        if action_type == 'move':
            return self._process_move_action(session, player, action_data)
        elif action_type == 'answer':
            return self._process_answer_action(session, player, action_data)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def _process_move_action(self, session, player, action_data):
        \"\"\"Process move action\"\"\"
        # Implement move logic here
        points = 10  # Example points
        
        # Update player score
        player.total_score += points
        player.save(update_fields=['total_score'])
        
        return {
            'action_result': 'move_successful',
            'points_earned': points,
            'new_score': player.total_score,
        }
    
    def _process_answer_action(self, session, player, action_data):
        \"\"\"Process answer action\"\"\"
        # Implement answer logic here
        correct = action_data.get('answer') == 'correct_answer'
        points = 20 if correct else 0
        
        # Update player score
        player.total_score += points
        player.actions_completed += 1
        player.save(update_fields=['total_score', 'actions_completed'])
        
        return {
            'action_result': 'answer_correct' if correct else 'answer_incorrect',
            'points_earned': points,
            'new_score': player.total_score,
            'correct': correct,
        }

class {{ game_class }}JoinView(BaseGameSessionView):
    \"\"\"View for joining {{ game_name }} sessions\"\"\"
    
    template_name = '{{ game_type }}/join.html'
    session_model = {{ game_class }}Session
    player_model = {{ game_class }}Player
""")
        
        context = Context({
            'game_name': self.game_name,
            'game_type': self.game_type,
            'game_class': self._to_class_name(self.game_name),
        })
        
        return template.render(context)
    
    def generate_plugin(self) -> str:
        """Generate plugin.py content"""
        template = Template("""
from games.engine import GamePlugin
from games.base.models import GameConfig
from .models import {{ game_class }}Session, {{ game_class }}Player

class {{ game_class }}Plugin(GamePlugin):
    \"\"\"Plugin for {{ game_name }}\"\"\"
    
    game_type = "{{ game_type }}"
    game_name = "{{ game_name }}"
    game_version = "1.0.0"
    
    requires_teams = False  # Set to True if game requires teams
    min_players = 1
    max_players = 8
    
    def get_game_config(self):
        return GameConfig(
            name=self.game_name,
            game_type=self.game_type,
            min_players=self.min_players,
            max_players=self.max_players,
            duration_minutes=30,
            supports_teams=self.requires_teams,
        )
    
    def get_session_model(self):
        return {{ game_class }}Session
    
    def get_player_model(self):
        return {{ game_class }}Player
    
    def get_view_urls(self):
        from django.urls import path
        from . import views
        
        return [
            path('{{ game_type }}/<str:session_code>/', views.{{ game_class }}GameView.as_view(), name='{{ game_type }}_game'),
            path('{{ game_type }}/<str:session_code>/join/', views.{{ game_class }}JoinView.as_view(), name='{{ game_type }}_join'),
            path('api/{{ game_type }}/<str:session_code>/action/', views.{{ game_class }}ActionAPI.as_view(), name='{{ game_type }}_action'),
        ]
    
    def validate_session_data(self, session_data):
        \"\"\"Validate session creation data\"\"\"
        # Add any game-specific validation here
        return True
    
    def on_session_created(self, session):
        \"\"\"Called after session is created\"\"\"
        # Initialize game-specific data
        session.game_settings = {
            'difficulty': 'normal',
            'time_limit': 1800,  # 30 minutes
        }
        session.save(update_fields=['game_settings'])
    
    def on_player_joined(self, session, player):
        \"\"\"Called after player joins\"\"\"
        # Initialize player-specific data
        player.game_progress = {
            'stage': 1,
            'completed_actions': [],
        }
        player.save(update_fields=['game_progress'])
""")
        
        context = Context({
            'game_name': self.game_name,
            'game_type': self.game_type,
            'game_class': self._to_class_name(self.game_name),
        })
        
        return template.render(context)
    
    def generate_templates(self) -> Dict[str, str]:
        """Generate template files"""
        
        # Base game template
        game_template = Template("""
{% extends "base.html" %}
{% load static %}

{% block title %}{{ game_name }} - Game{% endblock %}

{% block content %}
<div class="game-container">
    <div class="game-header">
        <h1>{{ game_name }}</h1>
        {% if session %}
            <p>Session: {{ session.session_code }}</p>
            <p>Stage: {{ current_stage }}</p>
        {% endif %}
        {% if player %}
            <p>Score: {{ player.total_score }}</p>
        {% endif %}
    </div>
    
    <div class="game-area" id="game-area">
        <!-- Game content will be loaded here -->
        <div class="game-placeholder">
            <h2>{{ game_name }} Game</h2>
            <p>Game interface will be implemented here.</p>
            
            {% if not player %}
                <a href="{{ session.get_absolute_url }}join/" class="btn btn-primary">Join Game</a>
            {% else %}
                <button onclick="startGame()" class="btn btn-success">Start Playing</button>
            {% endif %}
        </div>
    </div>
</div>

<script>
// Game-specific JavaScript
const gameData = {
    sessionCode: '{{ session.session_code|default:"" }}',
    playerId: {{ player.id|default:"null" }},
    gameType: '{{ game_type }}',
};

function startGame() {
    // Implement game start logic
    console.log('Starting {{ game_name }}');
}

// Add more game-specific functions here
</script>
{% endblock %}
""")
        
        # Join template
        join_template = Template("""
{% extends "base.html" %}

{% block title %}Join {{ game_name }}{% endblock %}

{% block content %}
<div class="join-container">
    <h1>Join {{ game_name }}</h1>
    
    <form method="post" class="join-form">
        {% csrf_token %}
        <div class="form-group">
            <label for="player_name">Your Name:</label>
            <input type="text" id="player_name" name="player_name" required>
        </div>
        
        <button type="submit" class="btn btn-primary">Join Game</button>
    </form>
</div>
{% endblock %}
""")
        
        context = Context({
            'game_name': self.game_name,
            'game_type': self.game_type,
        })
        
        return {
            'game.html': game_template.render(context),
            'join.html': join_template.render(context),
        }
    
    def generate_urls(self) -> str:
        """Generate urls.py content"""
        template = Template("""
from django.urls import path, include
from . import views

app_name = '{{ app_name }}'

urlpatterns = [
    path('', views.{{ game_class }}GameView.as_view(), name='home'),
    path('<str:session_code>/', views.{{ game_class }}GameView.as_view(), name='game'),
    path('<str:session_code>/join/', views.{{ game_class }}JoinView.as_view(), name='join'),
    path('api/<str:session_code>/action/', views.{{ game_class }}ActionAPI.as_view(), name='action_api'),
]
""")
        
        context = Context({
            'game_class': self._to_class_name(self.game_name),
            'app_name': self.app_name,
        })
        
        return template.render(context)
    
    def generate_admin(self) -> str:
        """Generate admin.py content"""
        template = Template("""
from django.contrib import admin
from .models import {{ game_class }}Session, {{ game_class }}Player, {{ game_class }}Action

@admin.register({{ game_class }}Session)
class {{ game_class }}SessionAdmin(admin.ModelAdmin):
    list_display = ['session_code', 'status', 'player_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['session_code']
    readonly_fields = ['session_code', 'created_at', 'updated_at']

@admin.register({{ game_class }}Player)
class {{ game_class }}PlayerAdmin(admin.ModelAdmin):
    list_display = ['player_name', 'session', 'total_score', 'is_active', 'joined_at']
    list_filter = ['is_active', 'joined_at']
    search_fields = ['player_name', 'session__session_code']

@admin.register({{ game_class }}Action)
class {{ game_class }}ActionAdmin(admin.ModelAdmin):
    list_display = ['player', 'action_type', 'points_earned', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['player__player_name']
""")
        
        context = Context({
            'game_class': self._to_class_name(self.game_name),
        })
        
        return template.render(context)
    
    def _to_class_name(self, name: str) -> str:
        """Convert name to PascalCase class name"""
        return ''.join(word.capitalize() for word in name.replace('-', ' ').replace('_', ' ').split())


class QuickGameCreator:
    """
    One-command game creation tool
    Creates a fully functional game in minutes
    """
    
    @staticmethod
    def create_quiz_game(name: str, questions: List[Dict]) -> str:
        """Create a complete quiz game"""
        game_type = name.lower().replace(' ', '_') + '_quiz'
        scaffold = GameScaffold(name, game_type)
        
        # Generate base structure
        structure = scaffold.create_game_structure()
        
        # Add quiz-specific enhancements
        structure['models'] += QuickGameCreator._get_quiz_models()
        structure['views'] += QuickGameCreator._get_quiz_views()
        
        return structure
    
    @staticmethod
    def create_strategy_game(name: str, scenarios: List[Dict]) -> str:
        """Create a complete strategy game"""
        game_type = name.lower().replace(' ', '_') + '_strategy'
        scaffold = GameScaffold(name, game_type)
        
        # Generate base structure
        structure = scaffold.create_game_structure()
        
        # Add strategy-specific enhancements
        structure['models'] += QuickGameCreator._get_strategy_models()
        structure['views'] += QuickGameCreator._get_strategy_views()
        
        return structure
    
    @staticmethod
    def _get_quiz_models() -> str:
        return """
class QuizQuestion(models.Model):
    session = models.ForeignKey({{ game_class }}Session, on_delete=models.CASCADE)
    question_text = models.TextField()
    options = models.JSONField()
    correct_answer = models.CharField(max_length=10)
    points = models.IntegerField(default=10)
    order = models.PositiveIntegerField()
"""
    
    @staticmethod
    def _get_quiz_views() -> str:
        return """
def get_current_question(self, session, player):
    \"\"\"Get current question for player\"\"\"
    answered_questions = player.actions.filter(action_type='answer').count()
    return session.questions.filter(order__gt=answered_questions).first()
"""
    
    @staticmethod
    def _get_strategy_models() -> str:
        return """
class StrategyScenario(models.Model):
    session = models.ForeignKey({{ game_class }}Session, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    choices = models.JSONField()
    order = models.PositiveIntegerField()
"""
    
    @staticmethod
    def _get_strategy_views() -> str:
        return """
def get_current_scenario(self, session):
    \"\"\"Get current scenario for session\"\"\"
    return session.scenarios.filter(order=session.current_scenario_order).first()
"""


# CLI Integration

class CreateGameCommand(BaseCommand):
    """
    Django management command for creating games
    Usage: python manage.py create_game "My New Game" quiz
    """
    
    help = 'Create a new game with scaffolding'
    
    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Game name')
        parser.add_argument('type', type=str, choices=['quiz', 'strategy', 'custom'], help='Game type')
        parser.add_argument('--app', type=str, help='App name (optional)')
    
    def handle(self, *args, **options):
        name = options['name']
        game_type = options['type']
        app_name = options.get('app')
        
        self.stdout.write(f"Creating {game_type} game: {name}")
        
        scaffold = GameScaffold(name, game_type, app_name)
        structure = scaffold.create_game_structure()
        
        # Output the generated code
        for file_type, content in structure.items():
            self.stdout.write(f"\n=== {file_type.upper()} ===")
            self.stdout.write(content)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {name} game scaffolding!')
        )