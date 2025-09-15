
from games.engine import GamePlugin
from games.base.models import GameConfig
from .models import CyberCitySession, CyberCityPlayer

class CyberCityProtectionSquadPlugin(GamePlugin):
    """Plugin for Cyber City Protection Squad"""
    
    game_type = "cyber_security"
    game_name = "Cyber City Protection Squad"
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
        return CyberCitySession
    
    def get_player_model(self):
        return CyberCityPlayer
    
    def get_view_urls(self):
        from django.urls import path
        from . import views
        
        return [
            path('cyber_security/<str:session_code>/', views.CyberCityGameView.as_view(), name='cyber_security_game'),
            path('cyber_security/<str:session_code>/avatar/', views.CyberCityAvatarView.as_view(), name='cyber_security_avatar'),
            path('api/cyber_security/<str:session_code>/action/', views.CyberCityActionAPI.as_view(), name='cyber_security_action'),
        ]
    
    def validate_session_data(self, session_data):
        """Validate session creation data"""
        # Add any game-specific validation here
        return True
    
    def on_session_created(self, session):
        """Called after session is created"""
        # Initialize cybersecurity game-specific data
        session.current_mission = 'password_fortress'
        session.mission_stage = 'intro'
        session.city_security_level = 0
        session.save()
    
    def on_player_joined(self, session, player):
        """Called after player joins"""
        # Initialize cybersecurity player-specific data
        player.current_challenge = 1
        player.challenges_completed = 0
        player.badges_earned = []
        player.save()
