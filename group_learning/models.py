from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json


class LearningModule(models.Model):
    """
    Curriculum modules/skills addressed by scenarios
    """
    MODULE_TYPES = [
        ('science', 'Science & Environment'),
        ('civics', 'Civics & Governance'),
        ('social', 'Social & Communication'),
        ('mathematics', 'Mathematics & Analytics'),
        ('language', 'Language & Literature'),
        ('life_skills', 'Life Skills & Ethics'),
    ]
    
    name = models.CharField(max_length=100, help_text="Name of the learning module")
    module_type = models.CharField(max_length=20, choices=MODULE_TYPES)
    description = models.TextField(help_text="What this module covers")
    grade_level = models.CharField(max_length=20, help_text="Target grade/age (e.g., '6-8', '9-12')")
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Learning Module"
        verbose_name_plural = "Learning Modules"
        ordering = ['module_type', 'name']
    
    def __str__(self):
        return f"{self.get_module_type_display()} - {self.name}"


class LearningObjective(models.Model):
    """
    Specific learning goals for scenarios
    """
    OBJECTIVE_TYPES = [
        ('knowledge', 'Knowledge & Understanding'),
        ('skills', 'Skills & Application'),
        ('attitudes', 'Attitudes & Values'),
        ('critical_thinking', 'Critical Thinking'),
        ('collaboration', 'Collaboration & Teamwork'),
        ('empathy', 'Empathy & Social Awareness'),
    ]
    
    title = models.CharField(max_length=200, help_text="Clear, concise learning objective")
    objective_type = models.CharField(max_length=20, choices=OBJECTIVE_TYPES)
    description = models.TextField(help_text="Detailed description of what students will learn")
    
    # Assessment criteria
    success_criteria = models.TextField(
        blank=True,
        help_text="How to measure if this objective was achieved"
    )
    
    learning_modules = models.ManyToManyField(
        LearningModule,
        blank=True,
        help_text="Curriculum modules this objective addresses"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Learning Objective"
        verbose_name_plural = "Learning Objectives"
        ordering = ['objective_type', 'title']
    
    def __str__(self):
        return f"{self.get_objective_type_display()}: {self.title}"


class Game(models.Model):
    """
    Top-level game container (e.g., "Climate Crisis India")
    """
    GAME_TYPES = [
        ('crisis_response', 'Crisis Response'),
        ('environmental', 'Environmental Challenge'),
        ('social_issue', 'Social Issue Resolution'),
        ('governance', 'Governance & Policy'),
        ('community_building', 'Community Building'),
    ]
    
    title = models.CharField(max_length=200, help_text="Game title (e.g., 'Climate Crisis India')")
    subtitle = models.CharField(max_length=300, blank=True, help_text="Descriptive subtitle")
    game_type = models.CharField(max_length=30, choices=GAME_TYPES)
    
    description = models.TextField(help_text="Overview of what this game teaches")
    context = models.TextField(help_text="Background context (e.g., Indian climate challenges)")
    
    # Game Configuration
    min_players = models.PositiveIntegerField(default=2, help_text="Minimum players needed")
    max_players = models.PositiveIntegerField(default=8, help_text="Maximum players allowed")
    estimated_duration = models.PositiveIntegerField(help_text="Estimated play time in minutes")
    
    # Educational Metadata
    target_age_min = models.PositiveIntegerField(help_text="Minimum recommended age")
    target_age_max = models.PositiveIntegerField(help_text="Maximum recommended age")
    difficulty_level = models.PositiveIntegerField(
        choices=[(1, 'Beginner'), (2, 'Intermediate'), (3, 'Advanced')],
        default=1
    )
    
    # Content
    cover_image = models.URLField(blank=True, help_text="Game cover image URL")
    introduction_text = models.TextField(help_text="Introduction shown to players")
    
    learning_objectives = models.ManyToManyField(
        LearningObjective,
        blank=True,
        help_text="What students will learn from this game"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Game"
        verbose_name_plural = "Games"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Role(models.Model):
    """
    Character roles that players can take (e.g., Collector, Farmer)
    """
    name = models.CharField(max_length=100, help_text="Role name (e.g., 'District Collector')")
    short_name = models.CharField(max_length=50, help_text="Short name for UI (e.g., 'Collector')")
    description = models.TextField(help_text="Role description and responsibilities")
    
    # Role characteristics
    authority_level = models.PositiveIntegerField(
        choices=[
            (1, 'Individual/Citizen'),
            (2, 'Community Leader'),
            (3, 'Local Official'),
            (4, 'Regional Authority'),
            (5, 'State/National Level')
        ],
        default=1,
        help_text="Level of authority/influence this role has"
    )
    
    expertise_areas = models.JSONField(
        default=list,
        help_text="List of expertise areas (e.g., ['agriculture', 'emergency_response'])"
    )
    
    # Visual representation
    icon = models.CharField(max_length=100, blank=True, help_text="Icon class or emoji")
    color = models.CharField(max_length=7, default="#007bff", help_text="Role color (hex)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ['-authority_level', 'name']
    
    def __str__(self):
        return self.name


class Scenario(models.Model):
    """
    Specific crisis/challenge situations within a game
    """
    SCENARIO_TYPES = [
        ('natural_disaster', 'Natural Disaster'),
        ('environmental_crisis', 'Environmental Crisis'),
        ('social_conflict', 'Social Conflict'),
        ('resource_shortage', 'Resource Shortage'),
        ('policy_decision', 'Policy Decision'),
        ('community_challenge', 'Community Challenge'),
    ]
    
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='scenarios')
    
    title = models.CharField(max_length=200, help_text="Scenario title (e.g., 'Monsoon Mayhem')")
    scenario_type = models.CharField(max_length=30, choices=SCENARIO_TYPES)
    
    # Scenario Content
    situation_description = models.TextField(
        help_text="Detailed description of the crisis situation"
    )
    urgency_level = models.PositiveIntegerField(
        choices=[
            (1, 'Low - Plan and Prepare'),
            (2, 'Medium - Act Soon'),
            (3, 'High - Immediate Action'),
            (4, 'Critical - Emergency Response')
        ],
        default=2
    )
    
    # Geographic/Cultural Context
    location = models.CharField(max_length=200, help_text="Where this scenario takes place")
    cultural_context = models.TextField(
        blank=True,
        help_text="Cultural, social, or regional context relevant to the scenario"
    )
    
    # Game Mechanics
    time_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time limit for decisions in minutes (null for no limit)"
    )
    
    required_roles = models.ManyToManyField(
        Role,
        help_text="Roles that must be present for this scenario"
    )
    
    learning_objectives = models.ManyToManyField(
        LearningObjective,
        blank=True,
        help_text="Specific learning goals for this scenario"
    )
    
    # Ordering and activation
    order = models.PositiveIntegerField(default=1, help_text="Order within the game")
    prerequisite_scenarios = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        help_text="Scenarios that must be completed first"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Scenario"
        verbose_name_plural = "Scenarios"
        ordering = ['game', 'order']
        unique_together = ['game', 'order']
    
    def __str__(self):
        return f"{self.game.title} - {self.title}"


class Action(models.Model):
    """
    Specific actions/choices available to roles in scenarios
    """
    ACTION_TYPES = [
        ('immediate', 'Immediate Response'),
        ('planning', 'Planning & Strategy'),
        ('communication', 'Communication & Coordination'),
        ('resource_allocation', 'Resource Allocation'),
        ('policy', 'Policy & Regulation'),
        ('community_engagement', 'Community Engagement'),
    ]
    
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='actions')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='actions')
    
    title = models.CharField(max_length=200, help_text="Action title (e.g., 'Evacuate town')")
    description = models.TextField(help_text="Detailed description of what this action involves")
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    
    # Action characteristics
    resource_cost = models.PositiveIntegerField(
        choices=[
            (1, 'Low Cost'),
            (2, 'Medium Cost'),
            (3, 'High Cost'),
            (4, 'Very High Cost')
        ],
        default=2
    )
    
    time_required = models.PositiveIntegerField(
        choices=[
            (1, 'Immediate'),
            (2, 'Short Term (Hours)'),
            (3, 'Medium Term (Days)'),
            (4, 'Long Term (Weeks+)')
        ],
        default=1
    )
    
    effectiveness_factors = models.JSONField(
        default=dict,
        help_text="Factors that affect action effectiveness (JSON)"
    )
    
    # Dependencies
    requires_other_roles = models.ManyToManyField(
        Role,
        blank=True,
        related_name='required_for_actions',
        help_text="Other roles that must cooperate for this action to succeed"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Action"
        verbose_name_plural = "Actions"
        ordering = ['scenario', 'role', 'action_type']
    
    def __str__(self):
        return f"{self.role.short_name}: {self.title}"


class Outcome(models.Model):
    """
    Results and consequences based on collective player actions
    """
    OUTCOME_TYPES = [
        ('success', 'Successful Resolution'),
        ('partial', 'Partial Success'),
        ('failure', 'Poor Outcome'),
        ('mixed', 'Mixed Results'),
        ('unexpected', 'Unexpected Consequences'),
    ]
    
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='outcomes')
    
    title = models.CharField(max_length=200, help_text="Outcome title")
    outcome_type = models.CharField(max_length=20, choices=OUTCOME_TYPES)
    
    # Outcome content
    description = models.TextField(help_text="What happens as a result")
    immediate_consequences = models.TextField(help_text="Immediate effects")
    long_term_effects = models.TextField(blank=True, help_text="Long-term consequences")
    
    # Scoring/Rating
    success_score = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 11)],
        default=5,
        help_text="Success rating (1-10)"
    )
    
    # Triggering conditions
    required_actions = models.ManyToManyField(
        Action,
        help_text="Actions that must be taken for this outcome"
    )
    
    # Alternative outcomes
    probability_weight = models.FloatField(
        default=1.0,
        help_text="Relative probability if conditions are met"
    )
    
    # Learning content
    learning_points = models.TextField(
        help_text="Key learning points highlighted by this outcome"
    )
    
    reflection_questions = models.JSONField(
        default=list,
        help_text="Questions for post-game reflection"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Outcome"
        verbose_name_plural = "Outcomes"
        ordering = ['-success_score', 'scenario']
    
    def __str__(self):
        return f"{self.scenario.title} - {self.title}"


# Session Management Models

class GameSession(models.Model):
    """
    Live multiplayer game sessions
    """
    SESSION_STATUS = [
        ('waiting', 'Waiting for Players'),
        ('in_progress', 'Game in Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='sessions')
    session_code = models.CharField(max_length=10, unique=True, help_text="Join code for players")
    
    # Session management
    facilitator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Teacher/facilitator running the session"
    )
    
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='waiting')
    current_scenario = models.ForeignKey(
        Scenario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Currently active scenario"
    )
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Settings
    allow_spectators = models.BooleanField(default=True)
    auto_assign_roles = models.BooleanField(default=True)
    
    session_data = models.JSONField(
        default=dict,
        help_text="Session state and progress data"
    )
    
    class Meta:
        verbose_name = "Game Session"
        verbose_name_plural = "Game Sessions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.game.title} - {self.session_code} ({self.status})"
    
    def generate_session_code(self):
        """Generate unique session code"""
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not GameSession.objects.filter(session_code=code).exists():
                self.session_code = code
                break
    
    def save(self, *args, **kwargs):
        if not self.session_code:
            self.generate_session_code()
        super().save(*args, **kwargs)


class PlayerAction(models.Model):
    """
    Individual player decisions during gameplay
    """
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='player_actions')
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    
    # Player identification (anonymous)
    player_name = models.CharField(max_length=100, help_text="Player's display name")
    player_session_id = models.CharField(max_length=100, help_text="Anonymous player ID")
    
    # Decision data
    decision_time = models.DateTimeField(auto_now_add=True)
    reasoning = models.TextField(blank=True, help_text="Player's explanation of their choice")
    
    # Context
    round_number = models.PositiveIntegerField(default=1)
    is_final_decision = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Player Action"
        verbose_name_plural = "Player Actions"
        ordering = ['session', 'round_number', 'decision_time']
        unique_together = ['session', 'scenario', 'role', 'round_number']
    
    def __str__(self):
        return f"{self.player_name} ({self.role.short_name}): {self.action.title}"


class ReflectionResponse(models.Model):
    """
    Post-game learning reflections and assessments
    """
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='reflections')
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    learning_objective = models.ForeignKey(LearningObjective, on_delete=models.CASCADE)
    
    # Player identification
    player_name = models.CharField(max_length=100)
    player_session_id = models.CharField(max_length=100)
    role_played = models.ForeignKey(Role, on_delete=models.CASCADE)
    
    # Reflection data
    question = models.TextField(help_text="The reflection question asked")
    response = models.TextField(help_text="Player's reflection response")
    
    # Self-assessment
    confidence_level = models.PositiveIntegerField(
        choices=[(i, f"{i}/5") for i in range(1, 6)],
        help_text="How confident the player feels about the learning objective"
    )
    
    engagement_level = models.PositiveIntegerField(
        choices=[(i, f"{i}/5") for i in range(1, 6)],
        help_text="How engaged the player felt during the scenario"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Reflection Response"
        verbose_name_plural = "Reflection Responses"
        ordering = ['session', '-created_at']
    
    def __str__(self):
        return f"{self.player_name} - {self.learning_objective.title}"
