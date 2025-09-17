
from django.db import models
from django.utils import timezone
from games.base.models import BaseGameSession, BaseGamePlayer

class CyberCitySession(BaseGameSession):
    """Game session for Cyber City Protection Squad"""
    
    # Mission-specific settings
    current_mission = models.CharField(max_length=50, default='password_fortress')
    mission_stage = models.CharField(max_length=50, default='intro')
    city_security_level = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'cyber_city_session'
        indexes = [
            models.Index(fields=['session_code', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def get_absolute_url(self):
        return f"/cyber-city/{self.session_code}/"

class CyberCityPlayer(BaseGamePlayer):
    """Player (Cyber Defender) for Cyber City Protection Squad"""
    
    session = models.ForeignKey(CyberCitySession, on_delete=models.CASCADE, related_name='players')
    
    # Avatar customization
    hero_nickname = models.CharField(max_length=50)
    suit_style = models.CharField(max_length=30, choices=[
        ('neon_knight', 'Neon Knight'),
        ('pixel_guard', 'Pixel Guard'),
        ('glitch_hunter', 'Glitch Hunter'),
    ], default='neon_knight')
    suit_color = models.CharField(max_length=7, default='#00FFFF')  # Hex color
    
    # Mission 1: Password Fortress progress
    current_challenge = models.PositiveIntegerField(default=1)
    challenges_completed = models.PositiveIntegerField(default=0)
    
    # Mission 2: Cyberbully Crisis progress  
    cyberbully_current_challenge = models.PositiveIntegerField(default=1)
    cyberbully_challenges_completed = models.PositiveIntegerField(default=0)
    
    # Overall progress
    missions_completed = models.JSONField(default=list)  # ['password_fortress', 'cyberbully_crisis']
    badges_earned = models.JSONField(default=list)
    
    # Performance tracking
    correct_answers = models.PositiveIntegerField(default=0)
    wrong_answers = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'cyber_city_player'
        unique_together = ['session', 'player_session_id']
        indexes = [
            models.Index(fields=['session', 'is_active']),
            models.Index(fields=['last_activity']),
        ]

class SecurityChallenge(models.Model):
    """Password security challenges for Mission 1"""
    
    challenge_number = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    question_text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C')])
    explanation = models.TextField()
    tessa_tip = models.TextField()  # AI Captain Tessa's educational tip
    
    class Meta:
        db_table = 'cyber_city_challenge'
        ordering = ['challenge_number']

class CyberbullyChallenge(models.Model):
    """Cyberbully identification challenges for Mission 2"""
    
    challenge_number = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    background_story = models.TextField()  # Setting description
    option_a = models.CharField(max_length=300)
    option_a_type = models.CharField(max_length=20, choices=[('friendly', 'Friendly'), ('bully', 'Bully')])
    option_b = models.CharField(max_length=300)
    option_b_type = models.CharField(max_length=20, choices=[('friendly', 'Friendly'), ('bully', 'Bully')])
    option_c = models.CharField(max_length=300)
    option_c_type = models.CharField(max_length=20, choices=[('friendly', 'Friendly'), ('bully', 'Bully')])
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C')])
    explanation = models.TextField()
    mentor_tip = models.TextField()  # Mentor's encouraging message
    mentor_voice_text = models.TextField()  # Text for voice synthesis
    
    class Meta:
        db_table = 'cyber_city_cyberbully_challenge'
        ordering = ['challenge_number']

class PlayerChallenge(models.Model):
    """Player's response to a security challenge"""
    
    player = models.ForeignKey(CyberCityPlayer, on_delete=models.CASCADE, related_name='challenge_responses')
    challenge = models.ForeignKey(SecurityChallenge, on_delete=models.CASCADE)
    answer_given = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C')])
    is_correct = models.BooleanField()
    points_earned = models.PositiveIntegerField(default=0)
    time_taken = models.PositiveIntegerField(help_text="Seconds taken to answer")
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cyber_city_player_challenge'
        unique_together = ['player', 'challenge']
        indexes = [
            models.Index(fields=['player', 'answered_at']),
            models.Index(fields=['challenge', 'is_correct']),
        ]

class PlayerCyberbullyChallenge(models.Model):
    """Player's response to a cyberbully challenge"""
    
    player = models.ForeignKey(CyberCityPlayer, on_delete=models.CASCADE, related_name='cyberbully_responses')
    challenge = models.ForeignKey(CyberbullyChallenge, on_delete=models.CASCADE)
    answer_given = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C')])
    is_correct = models.BooleanField()
    points_earned = models.PositiveIntegerField(default=0)
    time_taken = models.PositiveIntegerField(help_text="Seconds taken to answer")
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cyber_city_player_cyberbully_challenge'
        unique_together = ['player', 'challenge']
        indexes = [
            models.Index(fields=['player', 'answered_at']),
            models.Index(fields=['challenge', 'is_correct']),
        ]

class CyberBadge(models.Model):
    """Badges that players can earn"""
    
    badge_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=20)  # Emoji or icon class
    unlock_condition = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'cyber_city_badge'
        
    def __str__(self):
        return f"{self.icon} {self.name}"
