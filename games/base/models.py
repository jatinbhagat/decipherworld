"""
DecipherWorld Game Framework - Base Models
Hybrid architecture: Core shared models with game-specific extensions
"""

from django.db import models
from django.utils import timezone
from django.urls import reverse
from abc import ABC, abstractmethod
import uuid


class BaseGameSession(models.Model):
    """
    Abstract base for all game sessions
    Provides common functionality while allowing game-specific extensions
    """
    class Meta:
        abstract = True
    
    # Core session fields (shared across all games)
    session_code = models.CharField(max_length=10, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Session lifecycle
    STATUS_CHOICES = [
        ('waiting', 'Waiting for Players'),
        ('in_progress', 'Game in Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    
    # Performance and scalability
    player_count = models.PositiveIntegerField(default=0)
    max_players = models.PositiveIntegerField(default=8)
    
    # Game-agnostic metadata
    session_data = models.JSONField(default=dict, help_text="Game-specific session configuration")
    
    def generate_session_code(self):
        """Generate unique session code"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def save(self, *args, **kwargs):
        if not self.session_code:
            self.session_code = self.generate_session_code()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Override in specific game implementations"""
        return f"/learn/session/{self.session_code}/"
    
    def is_joinable(self):
        """Can new players join this session?"""
        return self.status == 'waiting' and self.player_count < self.max_players
    
    def is_active(self):
        """Is the session currently active?"""
        return self.status in ['waiting', 'in_progress']


class BaseGamePlayer(models.Model):
    """
    Abstract base for game players
    Links players to sessions with common functionality
    """
    class Meta:
        abstract = True
    
    # Player identification
    player_name = models.CharField(max_length=100)
    player_session_id = models.CharField(max_length=32, help_text="Browser session identifier")
    
    # Player state
    joined_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Performance and scoring
    total_score = models.IntegerField(default=0)
    actions_completed = models.PositiveIntegerField(default=0)
    
    # Flexible player data
    player_data = models.JSONField(default=dict, help_text="Game-specific player information")
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def is_online(self):
        """Is player considered online? (active within 5 minutes)"""
        cutoff = timezone.now() - timezone.timedelta(minutes=5)
        return self.last_activity > cutoff


class GameAction(models.Model):
    """
    Generic action system for all games
    Flexible enough to handle different game mechanics
    """
    # Action identification
    action_id = models.UUIDField(default=uuid.uuid4, unique=True)
    action_type = models.CharField(max_length=50, help_text="Type of action (answer, move, vote, etc.)")
    
    # Action metadata
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(help_text="Action-specific data")
    
    # Results
    points_earned = models.IntegerField(default=0)
    success = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['created_at']),
        ]


class GameMetrics(models.Model):
    """
    Performance metrics and analytics for games
    Helps with optimization and game balancing
    """
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    metric_data = models.JSONField(default=dict)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['metric_name', 'recorded_at']),
        ]


# Game Framework Interfaces (ABC for type safety)

class GameInterface(ABC):
    """
    Abstract interface that all games must implement
    Ensures consistency across different game types
    """
    
    @abstractmethod
    def get_game_config(self):
        """Return game configuration"""
        pass
    
    @abstractmethod
    def create_session(self, **kwargs):
        """Create a new game session"""
        pass
    
    @abstractmethod
    def join_session(self, session, player_data):
        """Add player to session"""
        pass
    
    @abstractmethod
    def process_action(self, session, player, action_data):
        """Process player action and return result"""
        pass
    
    @abstractmethod
    def get_session_state(self, session):
        """Get current session state for display"""
        pass
    
    @abstractmethod
    def is_session_complete(self, session):
        """Check if session is complete"""
        pass


class GameConfig:
    """
    Configuration container for games
    Standardizes game setup across different types
    """
    def __init__(self, name, game_type, min_players=1, max_players=8, 
                 duration_minutes=30, supports_teams=False, **kwargs):
        self.name = name
        self.game_type = game_type
        self.min_players = min_players
        self.max_players = max_players
        self.duration_minutes = duration_minutes
        self.supports_teams = supports_teams
        self.extra_config = kwargs
    
    def to_dict(self):
        return {
            'name': self.name,
            'game_type': self.game_type,
            'min_players': self.min_players,
            'max_players': self.max_players,
            'duration_minutes': self.duration_minutes,
            'supports_teams': self.supports_teams,
            **self.extra_config
        }