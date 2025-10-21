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
        ('constitution_challenge', 'Constitution Challenge'),
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
    
    def get_player_count(self):
        """Get current number of active players in session"""
        return self.player_actions.values('player_session_id').distinct().count()
    
    def get_active_players(self):
        """Get list of active players with their roles"""
        from django.db.models import Max
        latest_actions = self.player_actions.select_related('role').values(
            'player_session_id', 'player_name'
        ).annotate(
            latest_action=Max('decision_time'),
            role_name=Max('role__short_name')
        ).order_by('player_name')
        return latest_actions
    
    def is_ready_to_start(self):
        """Check if session has minimum players to start"""
        return self.get_player_count() >= self.game.min_players
    
    def get_role_coverage(self):
        """Check which roles are filled in the session"""
        filled_roles = self.player_actions.values_list('role_id', flat=True).distinct()
        required_roles = []
        if self.current_scenario:
            required_roles = self.current_scenario.required_roles.values_list('id', flat=True)
        
        return {
            'filled': filled_roles,
            'required': list(required_roles),
            'missing': [r for r in required_roles if r not in filled_roles]
        }
    
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


# Constitution Challenge Game Models

class ConstitutionQuestion(models.Model):
    """
    Multiple choice questions about governance and constitution for Build Your Country game
    """
    QUESTION_CATEGORIES = [
        ('leadership', 'How Leaders Are Chosen'),
        ('rules', 'Who Makes Rules'),
        ('rights', 'Citizens Rights & Freedoms'),
        ('justice', 'Justice & Fairness'),
        ('participation', 'Citizen Participation'),
        ('checks', 'Checks & Balances'),
    ]
    
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='constitution_questions')
    
    # Question Content
    question_text = models.TextField(help_text="The main question asked to teams")
    category = models.CharField(max_length=20, choices=QUESTION_CATEGORIES)
    
    # Question Context
    scenario_context = models.TextField(
        blank=True,
        help_text="Brief scenario setup (e.g., 'Your new country needs to decide...')"
    )
    
    # Visual/Learning Content
    learning_module_title = models.CharField(max_length=200, blank=True, help_text="Title for the learning pop-up")
    learning_module_content = models.TextField(
        blank=True,
        help_text="1-2 paragraphs explaining the governance concept"
    )
    learning_module_comic_url = models.URLField(blank=True, help_text="Optional comic/illustration URL")
    
    # Game Mechanics
    order = models.PositiveIntegerField(help_text="Question sequence order")
    time_limit = models.PositiveIntegerField(
        default=60,
        help_text="Time limit for teams to answer in seconds"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Constitution Question"
        verbose_name_plural = "Constitution Questions"
        ordering = ['game', 'order']
        unique_together = ['game', 'order']
    
    def __str__(self):
        return f"{self.game.title} - Q{self.order}: {self.question_text[:50]}..."


class ConstitutionOption(models.Model):
    """
    Answer choices for constitution questions with scoring and feedback
    """
    question = models.ForeignKey(ConstitutionQuestion, on_delete=models.CASCADE, related_name='options')
    
    # Option Content
    option_text = models.TextField(help_text="The answer choice text")
    option_letter = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        help_text="Option identifier (A, B, C, D)"
    )
    
    # Scoring & Feedback
    score_value = models.IntegerField(
        help_text="Points awarded for this choice (-5 to +5 typical range)"
    )
    feedback_message = models.TextField(
        help_text="Short explanation of why this choice earns/loses points"
    )
    
    # Educational Context
    governance_principle = models.CharField(
        max_length=100,
        blank=True,
        help_text="The governance principle this choice represents (e.g., 'Democracy', 'Checks & Balances')"
    )
    
    # Dynamic Impact Content (Choice-Specific)
    governance_impact = models.TextField(
        blank=True,
        help_text="How this specific choice affects the country's governance and democratic institutions"
    )
    score_reasoning = models.TextField(
        blank=True,
        help_text="Why this specific choice increases/decreases the governance score"
    )
    country_state_changes = models.TextField(
        blank=True,
        help_text="How this choice affects city growth, population, economic prosperity, etc."
    )
    societal_impact = models.TextField(
        blank=True,
        help_text="Impact of this choice on citizens, rights, freedoms, and social harmony"
    )
    
    # Visual Styling
    color_class = models.CharField(
        max_length=20,
        default='blue',
        choices=[
            ('blue', 'Blue'),
            ('green', 'Green'),
            ('yellow', 'Yellow'),
            ('red', 'Red'),
            ('purple', 'Purple'),
            ('orange', 'Orange'),
        ],
        help_text="Color for the answer button"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Constitution Option"
        verbose_name_plural = "Constitution Options"
        ordering = ['question', 'option_letter']
        unique_together = ['question', 'option_letter']
    
    def __str__(self):
        return f"{self.question.game.title} - Q{self.question.order}{self.option_letter}: {self.option_text[:30]}..."


class ConstitutionTeam(models.Model):
    """
    Team data for constitution challenge games
    """
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='constitution_teams')
    
    # Team Identity
    team_name = models.CharField(max_length=100, help_text="Team's chosen country name")
    team_avatar = models.CharField(
        max_length=50,
        default='🏛️',
        help_text="Emoji or icon representing the team"
    )
    country_color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text="Team's chosen color (hex code)"
    )
    flag_emoji = models.CharField(
        max_length=10,
        default='🏴',
        help_text="Team's chosen flag emoji"
    )
    
    # Game Progress
    current_question = models.ForeignKey(
        ConstitutionQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Current question the team is answering"
    )
    total_score = models.IntegerField(default=0, help_text="Team's total governance score")
    questions_completed = models.PositiveIntegerField(default=0)
    
    # Team State
    is_completed = models.BooleanField(default=False)
    completion_time = models.DateTimeField(null=True, blank=True)
    
    # Team Collaboration Data
    team_data = models.JSONField(
        default=dict,
        help_text="Store team member votes, discussion data, etc."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Constitution Team"
        verbose_name_plural = "Constitution Teams"
        ordering = ['-total_score', 'completion_time']
    
    def __str__(self):
        return f"{self.team_name} (Score: {self.total_score})"
    
    def get_governance_level(self):
        """Return the governance level description based on score"""
        if self.total_score <= 0:
            return {"level": "struggling_settlement", "description": "Struggling Settlement", "emoji": "🏚️"}
        elif self.total_score <= 6:
            return {"level": "simple_village", "description": "Simple Village", "emoji": "🏘️"}
        elif self.total_score <= 12:
            return {"level": "growing_town", "description": "Growing Town", "emoji": "🏪"}
        elif self.total_score <= 18:
            return {"level": "thriving_city", "description": "Thriving City", "emoji": "🏙️"}
        elif self.total_score <= 24:
            return {"level": "great_capital", "description": "Great Capital", "emoji": "🌆"}
        else:
            return {"level": "ideal_nation", "description": "Ideal Nation", "emoji": "🌟"}
    
    def get_rank_in_session(self):
        """Get team's current rank in the session"""
        better_teams = ConstitutionTeam.objects.filter(
            session=self.session,
            total_score__gt=self.total_score
        ).count()
        return better_teams + 1


class CountryState(models.Model):
    """
    Visual and narrative state of a team's country based on their governance choices
    """
    team = models.OneToOneField(ConstitutionTeam, on_delete=models.CASCADE, related_name='country_state')
    
    # Visual State
    current_city_level = models.CharField(
        max_length=30,
        choices=[
            ('struggling_settlement', 'Struggling Settlement - Dull huts, rain'),
            ('simple_village', 'Simple Village - Hamlet, dusty roads'),
            ('growing_town', 'Growing Town - School, first court'),
            ('thriving_city', 'Thriving City - Public square, parks'),
            ('great_capital', 'Great Capital - Landmarks, monuments'),
            ('ideal_nation', 'Ideal Nation - Radiant metropolis, parade'),
        ],
        default='struggling_settlement'
    )
    
    # Governance Metrics (for visual meter)
    democracy_score = models.IntegerField(default=0, help_text="Democratic participation level")
    fairness_score = models.IntegerField(default=0, help_text="Justice and fairness level")
    freedom_score = models.IntegerField(default=0, help_text="Individual freedoms level")
    stability_score = models.IntegerField(default=0, help_text="Political stability level")
    
    # Unlocked Features (buildings, monuments, etc.)
    unlocked_features = models.JSONField(
        default=list,
        help_text="List of visual features unlocked (e.g., ['school', 'courthouse', 'parliament'])"
    )
    
    # Granular Visual Elements for Immersive City
    visual_elements = models.JSONField(
        default=dict,
        help_text="""
        Detailed visual state for animated city rendering:
        {
            'terrain': {'type': 'barren|green|fertile', 'features': ['river', 'hills']},
            'buildings': {
                'residential': [{'type': 'hut|house|apartment', 'position': [x,y], 'level': 1-3}],
                'civic': [{'type': 'school|courthouse|parliament', 'position': [x,y], 'status': 'building|complete'}],
                'commercial': [{'type': 'market|mall', 'position': [x,y]}]
            },
            'citizens': {
                'population': 50,
                'mood': 'happy|neutral|angry',
                'activities': ['celebration', 'protest', 'work']
            },
            'weather': {'type': 'sunny|cloudy|rainy|stormy', 'effects': ['rainbow', 'lightning']},
            'animations': ['fireworks', 'construction', 'parade'],
            'sound_cues': ['cheers', 'construction_sound', 'celebration_music']
        }
        """
    )
    
    # Narrative Elements
    country_description = models.TextField(
        blank=True,
        help_text="Generated description of the country based on choices"
    )
    achievement_badges = models.JSONField(
        default=list,
        help_text="Special badges earned (e.g., ['democratic_leader', 'fair_justice'])"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Country State"
        verbose_name_plural = "Country States"
    
    def __str__(self):
        return f"{self.team.team_name} - {self.get_current_city_level_display()}"
    
    def update_from_score(self, new_total_score):
        """Update visual state based on new total score"""
        # Update city level
        governance_level = self.team.get_governance_level()
        self.current_city_level = governance_level['level']
        
        # Update governance metrics (distribute score across metrics)
        base_score = max(0, new_total_score // 4)  # Base level for each metric
        self.democracy_score = min(10, base_score + (new_total_score % 4))
        self.fairness_score = min(10, base_score)
        self.freedom_score = min(10, base_score)
        self.stability_score = min(10, base_score)
        
        # Update unlocked features based on score thresholds
        features = []
        if new_total_score >= 3:
            features.append('basic_housing')
        if new_total_score >= 7:
            features.extend(['school', 'marketplace'])
        if new_total_score >= 13:
            features.extend(['courthouse', 'hospital'])
        if new_total_score >= 19:
            features.extend(['parliament', 'university'])
        if new_total_score >= 25:
            features.extend(['monuments', 'gardens', 'celebration'])
            
        self.unlocked_features = features
        
        # Update detailed visual elements for immersive rendering
        self._update_visual_elements(new_total_score)
        self.save()
    
    def _update_visual_elements(self, score):
        """Update granular visual elements based on score"""
        import random
        
        # Initialize default structure if empty
        if not self.visual_elements:
            self.visual_elements = {
                'terrain': {'type': 'barren', 'features': []},
                'buildings': {'residential': [], 'civic': [], 'commercial': []},
                'citizens': {'population': 10, 'mood': 'neutral', 'activities': []},
                'weather': {'type': 'cloudy', 'effects': []},
                'animations': [],
                'sound_cues': []
            }
        
        # Terrain evolution based on score
        terrain_types = ['barren', 'dusty', 'green', 'lush', 'fertile', 'paradise']
        terrain_index = min(5, score // 5)
        self.visual_elements['terrain']['type'] = terrain_types[terrain_index]
        
        # Add terrain features
        terrain_features = []
        if score >= 5:
            terrain_features.append('river')
        if score >= 15:
            terrain_features.extend(['hills', 'trees'])
        if score >= 25:
            terrain_features.extend(['gardens', 'fountains'])
        self.visual_elements['terrain']['features'] = terrain_features
        
        # Buildings progression
        buildings = {'residential': [], 'civic': [], 'commercial': []}
        
        # Residential buildings
        housing_count = min(8, score // 3)
        for i in range(housing_count):
            house_type = 'hut' if score < 10 else 'house' if score < 20 else 'apartment'
            buildings['residential'].append({
                'type': house_type,
                'position': [random.randint(10, 90), random.randint(60, 85)],
                'level': min(3, (score // 8) + 1)
            })
        
        # Civic buildings
        if score >= 7:
            buildings['civic'].append({
                'type': 'school',
                'position': [25, 45],
                'status': 'complete'
            })
        if score >= 13:
            buildings['civic'].extend([
                {'type': 'courthouse', 'position': [75, 45], 'status': 'complete'},
                {'type': 'hospital', 'position': [50, 35], 'status': 'complete'}
            ])
        if score >= 19:
            buildings['civic'].extend([
                {'type': 'parliament', 'position': [50, 25], 'status': 'complete'},
                {'type': 'university', 'position': [80, 30], 'status': 'complete'}
            ])
        
        # Commercial buildings
        if score >= 7:
            buildings['commercial'].append({'type': 'marketplace', 'position': [30, 55]})
        if score >= 20:
            buildings['commercial'].append({'type': 'mall', 'position': [70, 55]})
            
        self.visual_elements['buildings'] = buildings
        
        # Citizens and mood
        population = min(200, 10 + (score * 3))
        mood = 'angry' if score < 0 else 'neutral' if score < 15 else 'happy'
        activities = []
        
        if score >= 20:
            activities.extend(['celebration', 'festivals'])
        elif score < 5:
            activities.append('protest')
        else:
            activities.append('work')
            
        self.visual_elements['citizens'] = {
            'population': population,
            'mood': mood,
            'activities': activities
        }
        
        # Weather based on governance quality
        weather_type = 'stormy' if score < 0 else 'cloudy' if score < 10 else 'partly_cloudy' if score < 20 else 'sunny'
        weather_effects = []
        if score >= 25:
            weather_effects.append('rainbow')
        elif score < 0:
            weather_effects.extend(['lightning', 'heavy_rain'])
            
        self.visual_elements['weather'] = {
            'type': weather_type,
            'effects': weather_effects
        }
        
        # Animations for this update
        animations = []
        sound_cues = []
        
        # Check if new buildings were unlocked
        new_features = set(self.unlocked_features) - set(getattr(self, '_previous_features', []))
        if new_features:
            animations.extend(['construction', 'building_complete'])
            sound_cues.extend(['construction_sound', 'achievement_bell'])
        
        # Celebration for high scores
        if score >= 20:
            animations.append('fireworks')
            sound_cues.append('celebration_music')
        elif score >= 15:
            animations.append('parade')
            sound_cues.append('cheers')
            
        self.visual_elements['animations'] = animations
        self.visual_elements['sound_cues'] = sound_cues
        
        # Store current features for next comparison
        self._previous_features = self.unlocked_features.copy()


class ConstitutionAnswer(models.Model):
    """
    Record of team answers to constitution questions
    """
    team = models.ForeignKey(ConstitutionTeam, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(ConstitutionQuestion, on_delete=models.CASCADE)
    chosen_option = models.ForeignKey(ConstitutionOption, on_delete=models.CASCADE)
    
    # Answer Metadata
    answer_time = models.DateTimeField(auto_now_add=True)
    time_taken = models.PositiveIntegerField(help_text="Seconds taken to answer")
    
    # Team Collaboration Data
    team_discussion = models.TextField(
        blank=True,
        help_text="Any team discussion or reasoning recorded"
    )
    vote_breakdown = models.JSONField(
        default=dict,
        help_text="How individual team members voted (if tracked)"
    )
    
    # Score Impact
    points_earned = models.IntegerField(help_text="Points this answer contributed")
    score_before = models.IntegerField(help_text="Team score before this answer")
    score_after = models.IntegerField(help_text="Team score after this answer")
    
    class Meta:
        verbose_name = "Constitution Answer"
        verbose_name_plural = "Constitution Answers"
        ordering = ['team', 'question__order']
        unique_together = ['team', 'question']
    
    def __str__(self):
        return f"{self.team.team_name} - Q{self.question.order}: {self.chosen_option.option_letter}"


class GameLearningModule(models.Model):
    """
    Enhanced learning modules that appear after answer submissions
    Scalable system for all game types with admin-friendly management
    """
    GAME_TYPES = [
        ('constitution_challenge', 'Constitution Challenge'),
        ('crisis_response', 'Crisis Response'),
        ('environmental', 'Environmental Challenge'),
        ('social_issue', 'Social Issue'),
        ('governance', 'Governance & Policy'),
        ('all_games', 'All Game Types'),
    ]
    
    TRIGGER_CONDITIONS = [
        ('question_based', 'Triggered by Specific Question'),
        ('option_based', 'Triggered by Specific Answer Option'),
        ('topic_based', 'Triggered by Constitutional Topic'),
        ('score_based', 'Triggered by Score Range'),
        ('always', 'Always Show After Any Answer'),
    ]
    
    DISPLAY_TIMING = [
        ('instant', 'Show Immediately'),
        ('delayed_3s', 'Show After 3 Seconds'),
        ('delayed_5s', 'Show After 5 Seconds'),
    ]
    
    # Basic Information
    title = models.CharField(
        max_length=200, 
        help_text="Module title (e.g., 'Understanding Democracy')"
    )
    game_type = models.CharField(
        max_length=30, 
        choices=GAME_TYPES,
        default='constitution_challenge',
        help_text="Which game type this module applies to"
    )
    
    # Content Fields
    principle_explanation = models.TextField(
        help_text="Main educational content explaining the principle or concept"
    )
    key_takeaways = models.TextField(
        help_text="Bullet points of key learnings (use • for bullets)"
    )
    historical_context = models.TextField(
        blank=True,
        help_text="Optional historical background or real-world examples"
    )
    real_world_example = models.TextField(
        blank=True,
        help_text="Optional contemporary example or case study"
    )
    
    # Enhanced Learning Module - Part 1: Action Reasoning
    action_impact_title = models.CharField(
        max_length=200,
        default="Impact of Your Decision",
        help_text="Title for the action reasoning section"
    )
    governance_impact = models.TextField(
        blank=True,
        help_text="How this choice affects the country's governance and democratic institutions"
    )
    score_reasoning = models.TextField(
        blank=True,
        help_text="Why the governance score increased/decreased with this choice"
    )
    country_state_changes = models.TextField(
        blank=True,
        help_text="How this choice affects city growth, population, economic prosperity, etc."
    )
    societal_impact = models.TextField(
        blank=True,
        help_text="Impact on citizens, rights, freedoms, and social harmony"
    )
    
    # Enhanced Learning Module - Part 2: Constitution Teaching
    constitution_topic_title = models.CharField(
        max_length=200,
        default="Learn from the Indian Constitution",
        help_text="Title for the constitution teaching section"
    )
    constitution_chapter = models.CharField(
        max_length=100,
        blank=True,
        choices=[
            ('introduction', 'Introduction to Constitutions'),
            ('making', 'Making of the Indian Constitution'),
            ('features', 'Key Features and Values'),
            ('government_branches', 'Branches of Government'),
            ('rights_duties', 'Citizens\' Rights and Duties'),
            ('inclusivity', 'Inclusivity and Pluralism'),
            ('living_document', 'Constitution as a Living Document'),
        ],
        help_text="Main constitutional topic this question relates to"
    )
    constitution_principle = models.TextField(
        blank=True,
        help_text="Core constitutional principle illustrated by this question (e.g., 'Separation of Powers', 'Fundamental Rights')"
    )
    constitution_explanation = models.TextField(
        blank=True,
        help_text="Detailed explanation of how this constitutional principle works in India"
    )
    constitution_article_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text="Specific Indian Constitution articles related to this topic (e.g., 'Article 14-18: Right to Equality')"
    )
    historical_constitutional_context = models.TextField(
        blank=True,
        help_text="Historical context of how this principle was included in the Indian Constitution"
    )
    
    # Trigger Configuration
    trigger_condition = models.CharField(
        max_length=20,
        choices=TRIGGER_CONDITIONS,
        default='question_based',
        help_text="What triggers this learning module to appear"
    )
    
    # Relationships for different trigger types
    trigger_question = models.ForeignKey(
        ConstitutionQuestion,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Show after this specific question (if question_based)"
    )
    trigger_option = models.ForeignKey(
        ConstitutionOption,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Show after this specific answer choice (if option_based)"
    )
    trigger_topic = models.CharField(
        max_length=50,
        blank=True,
        choices=ConstitutionQuestion.QUESTION_CATEGORIES,
        help_text="Show for this constitutional topic (if topic_based)"
    )
    
    # Score-based triggers
    min_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Minimum team score to trigger (if score_based)"
    )
    max_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum team score to trigger (if score_based)"
    )
    
    # Display Configuration
    display_timing = models.CharField(
        max_length=20,
        choices=DISPLAY_TIMING,
        default='instant',
        help_text="When to show the module after trigger condition is met"
    )
    is_skippable = models.BooleanField(
        default=True,
        help_text="Can users skip this learning module?"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Is this module currently active?"
    )
    
    # Performance-based content variation
    low_performance_content = models.TextField(
        blank=True,
        help_text="Alternative content for teams with low scores (optional)"
    )
    high_performance_content = models.TextField(
        blank=True,
        help_text="Alternative content for teams with high scores (optional)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Admin user who created this module"
    )
    
    # Usage analytics
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="How many times this module has been shown"
    )
    skip_count = models.PositiveIntegerField(
        default=0,
        help_text="How many times this module was skipped"
    )
    
    class Meta:
        verbose_name = "Learning Module"
        verbose_name_plural = "Learning Modules"
        ordering = ['game_type', 'title']
        
    def __str__(self):
        return f"{self.get_game_type_display()} - {self.title}"
    
    def get_content_for_team(self, team_score):
        """
        Return appropriate content based on team performance
        """
        if self.low_performance_content and team_score < 5:
            return {
                'title': self.title,
                'principle_explanation': self.low_performance_content,
                'key_takeaways': self.key_takeaways,
                'historical_context': self.historical_context,
                'real_world_example': self.real_world_example,
            }
        elif self.high_performance_content and team_score > 15:
            return {
                'title': self.title,
                'principle_explanation': self.high_performance_content,
                'key_takeaways': self.key_takeaways,
                'historical_context': self.historical_context,
                'real_world_example': self.real_world_example,
            }
        else:
            return {
                'title': self.title,
                'principle_explanation': self.principle_explanation,
                'key_takeaways': self.key_takeaways,
                'historical_context': self.historical_context,
                'real_world_example': self.real_world_example,
            }
    
    def should_trigger(self, question=None, option=None, topic=None, team_score=None):
        """
        Determine if this module should be triggered based on conditions
        """
        if not self.is_enabled:
            return False
            
        if self.trigger_condition == 'always':
            return True
        elif self.trigger_condition == 'question_based':
            return self.trigger_question == question
        elif self.trigger_condition == 'option_based':
            return self.trigger_option == option
        elif self.trigger_condition == 'topic_based':
            return self.trigger_topic == topic
        elif self.trigger_condition == 'score_based':
            if team_score is None:
                return False
            min_ok = self.min_score is None or team_score >= self.min_score
            max_ok = self.max_score is None or team_score <= self.max_score
            return min_ok and max_ok
        
        return False
    
    def record_view(self, was_skipped=False):
        """
        Record analytics for this module usage
        """
        self.view_count += 1
        if was_skipped:
            self.skip_count += 1
        self.save(update_fields=['view_count', 'skip_count'])


# ==================================================================================
# CLIMATE CHANGE SIMULATION GAME MODELS
# ==================================================================================

class ClimateGame(Game):
    """
    Climate Change Simulation Game - extends base Game model
    Tracks society-level metrics that change based on player decisions
    """
    # Society Metrics (0-100 scale)
    climate_resilience_meter = models.IntegerField(
        default=50, 
        help_text="Climate adaptation and mitigation progress (0-100)"
    )
    gdp_meter = models.IntegerField(
        default=50, 
        help_text="Economic health and growth (0-100)"
    )
    public_morale_meter = models.IntegerField(
        default=50, 
        help_text="Citizen satisfaction and social cohesion (0-100)"
    )
    environmental_health_meter = models.IntegerField(
        default=50, 
        help_text="Air, water, and ecosystem quality (0-100)"
    )
    
    class Meta:
        verbose_name = "Climate Game"
        verbose_name_plural = "Climate Games"


class ClimateScenario(models.Model):
    """
    Individual scenarios for each round (Delhi Air Pollution, Mumbai Floods, etc.)
    """
    SCENARIO_ROUNDS = [
        (1, 'Round 1: Delhi Air Pollution Crisis'),
        (2, 'Round 2: Mumbai Floods'),
        (3, 'Round 3: Chennai Water Shortage'),
        (4, 'Round 4: Migration & Heatwave'),
        (5, 'Round 5: National Election/Policy'),
    ]
    
    game = models.ForeignKey(ClimateGame, on_delete=models.CASCADE, related_name='climate_scenarios')
    round_number = models.IntegerField(choices=SCENARIO_ROUNDS)
    title = models.CharField(max_length=200, help_text="e.g., 'Delhi Air Pollution Crisis'")
    
    # Scenario Content
    context_description = models.TextField(help_text="Background situation and stakes")
    background_image = models.URLField(
        blank=True, 
        help_text="URL to India-specific background image"
    )
    news_quotes = models.JSONField(
        default=list,
        help_text="Array of fake news quotes to set atmosphere"
    )
    potential_consequences = models.JSONField(
        default=list,
        help_text="2-3 potential consequences if unaddressed"
    )
    
    # Timing
    presentation_duration = models.IntegerField(
        default=90, 
        help_text="Seconds to present scenario"
    )
    response_duration = models.IntegerField(
        default=60, 
        help_text="Seconds for players to respond"
    )
    feedback_duration = models.IntegerField(
        default=120, 
        help_text="Seconds to show results and feedback"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Climate Scenario"
        verbose_name_plural = "Climate Scenarios"
        ordering = ['round_number']
        unique_together = ['game', 'round_number']
    
    def __str__(self):
        return f"Round {self.round_number}: {self.title}"


class ClimateQuestion(models.Model):
    """
    Role-specific questions within each scenario
    Each scenario has 5 questions (one per role)
    """
    ROLE_CHOICES = [
        ('government', 'Government Official'),
        ('business', 'Business Owner'),
        ('farmer', 'Farmer'),
        ('urban_citizen', 'Urban Citizen'),
        ('ngo_worker', 'NGO Worker'),
    ]
    
    scenario = models.ForeignKey(ClimateScenario, on_delete=models.CASCADE, related_name='questions')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    question_text = models.TextField(help_text="The decision prompt for this role")
    
    # Optional: Additional context specific to this role
    role_context = models.TextField(
        blank=True, 
        help_text="Additional background specific to this role's perspective"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Climate Question"
        verbose_name_plural = "Climate Questions"
        ordering = ['scenario__round_number', 'role']
        unique_together = ['scenario', 'role']
    
    def __str__(self):
        return f"{self.scenario.title} - {self.get_role_display()}"


class ClimateOption(models.Model):
    """
    Individual answer options for each role question
    Each question has 4 options (a, b, c, d)
    """
    OPTION_LETTERS = [
        ('a', 'Option A'),
        ('b', 'Option B'),
        ('c', 'Option C'),
        ('d', 'Option D'),
    ]
    
    question = models.ForeignKey(ClimateQuestion, on_delete=models.CASCADE, related_name='options')
    option_letter = models.CharField(max_length=1, choices=OPTION_LETTERS)
    option_text = models.TextField(help_text="The action/decision this option represents")
    immediate_consequence = models.TextField(help_text="Bold text describing trade-offs and risks")
    
    # Outcome Logic - how this choice affects society meters
    outcome_logic = models.JSONField(
        default=dict,
        help_text="Impact on climate_resilience, gdp, public_morale, environmental_health"
    )
    
    # Analytics
    selection_count = models.IntegerField(default=0, help_text="How many times this option was chosen")
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Climate Option"
        verbose_name_plural = "Climate Options"
        ordering = ['question__scenario__round_number', 'question__role', 'option_letter']
        unique_together = ['question', 'option_letter']
    
    def __str__(self):
        return f"{self.question} - Option {self.option_letter.upper()}"
    
    def increment_selection(self):
        """Track analytics when this option is selected"""
        self.selection_count += 1
        self.save(update_fields=['selection_count'])


class ClimateGameSession(GameSession):
    """
    Live climate game session - extends base GameSession
    Tracks real-time society meters and round progress
    """
    climate_game = models.ForeignKey(ClimateGame, on_delete=models.CASCADE, related_name='climate_sessions')
    
    # Current Game State
    current_round = models.IntegerField(default=1, help_text="Current scenario round (1-5)")
    current_phase = models.CharField(
        max_length=20,
        choices=[
            ('lobby', 'Waiting in Lobby'),
            ('scenario_intro', 'Scenario Introduction'),
            ('question_phase', 'Question Response'),
            ('results_feedback', 'Results & Feedback'),
            ('round_complete', 'Round Complete'),
            ('game_complete', 'Game Complete'),
        ],
        default='lobby'
    )
    
    # Real-time Society Meters (evolve during game)
    current_climate_resilience = models.IntegerField(default=50)
    current_gdp = models.IntegerField(default=50)
    current_public_morale = models.IntegerField(default=50)
    current_environmental_health = models.IntegerField(default=50)
    
    # Round timing
    round_start_time = models.DateTimeField(null=True, blank=True)
    phase_start_time = models.DateTimeField(null=True, blank=True)
    
    # Timer functionality
    round_duration_minutes = models.IntegerField(default=10, help_text="Duration for each round in minutes")
    question_timer_enabled = models.BooleanField(default=True, help_text="Enable timer for question phase")
    current_timer_end = models.DateTimeField(null=True, blank=True, help_text="When current timer expires")
    
    class Meta:
        verbose_name = "Climate Game Session"
        verbose_name_plural = "Climate Game Sessions"
    
    def start_new_round(self, round_number):
        """Initialize a new scenario round"""
        self.current_round = round_number
        self.current_phase = 'scenario_intro'
        self.round_start_time = timezone.now()
        self.phase_start_time = timezone.now()
        
        # Don't set current_scenario - it's for base Scenario model, not ClimateScenario
        # Climate scenarios are accessed via self.climate_game.climate_scenarios.filter(round_number=round_number)
        
        self.save()
    
    def advance_phase(self, new_phase):
        """Move to next phase of current round"""
        self.current_phase = new_phase
        self.phase_start_time = timezone.now()
        self.save()
    
    def update_meters(self, meter_changes):
        """Apply meter changes from player decisions"""
        self.current_climate_resilience = max(0, min(100, 
            self.current_climate_resilience + meter_changes.get('climate_resilience', 0)))
        self.current_gdp = max(0, min(100, 
            self.current_gdp + meter_changes.get('gdp', 0)))
        self.current_public_morale = max(0, min(100, 
            self.current_public_morale + meter_changes.get('public_morale', 0)))
        self.current_environmental_health = max(0, min(100, 
            self.current_environmental_health + meter_changes.get('environmental_health', 0)))
        self.save()
    
    def get_meter_status(self):
        """Return current meter values as dict"""
        return {
            'climate_resilience': self.current_climate_resilience,
            'gdp': self.current_gdp,
            'public_morale': self.current_public_morale,
            'environmental_health': self.current_environmental_health,
        }
    
    def get_active_player_count(self):
        """Return count of distinct active players in this session"""
        return self.climate_responses.values('player_session_id').distinct().count()
    
    def get_active_players_list(self):
        """Return list of active players with their details"""
        return self.climate_responses.values(
            'player_name', 'player_session_id', 'assigned_role'
        ).distinct().order_by('player_name')
    
    def start_timer(self, duration_minutes=None):
        """Start timer for current phase"""
        if duration_minutes is None:
            duration_minutes = self.round_duration_minutes
        
        self.current_timer_end = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.save()
    
    def get_timer_info(self):
        """Get current timer information"""
        if not self.current_timer_end:
            return {
                'enabled': False,
                'seconds_remaining': 0,
                'expired': True
            }
        
        now = timezone.now()
        seconds_remaining = max(0, (self.current_timer_end - now).total_seconds())
        
        return {
            'enabled': self.question_timer_enabled,
            'seconds_remaining': int(seconds_remaining),
            'expired': seconds_remaining <= 0,
            'end_time': self.current_timer_end.isoformat() if self.current_timer_end else None
        }
    
    def set_timer_duration(self, minutes):
        """Set timer duration for rounds"""
        self.round_duration_minutes = minutes
        self.save()


class ClimatePlayerResponse(models.Model):
    """
    Individual player responses to climate scenarios
    Standalone model for climate-specific data
    """
    climate_session = models.ForeignKey(ClimateGameSession, on_delete=models.CASCADE, related_name='climate_responses')
    climate_scenario = models.ForeignKey(ClimateScenario, on_delete=models.CASCADE, null=True, blank=True)
    selected_option = models.ForeignKey(ClimateOption, on_delete=models.CASCADE, null=True, blank=True)
    
    # Player identification (anonymous)
    player_name = models.CharField(max_length=100, help_text="Player's display name")
    player_session_id = models.CharField(max_length=100, help_text="Anonymous player ID")
    
    # Player assignment for this session
    assigned_role = models.CharField(
        max_length=20, 
        choices=ClimateQuestion.ROLE_CHOICES,
        help_text="Role assigned to this player for entire game"
    )
    
    # Timing analytics
    response_time = models.FloatField(help_text="Seconds taken to respond")
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Decision context
    round_number = models.PositiveIntegerField(help_text="Which round this response is for")
    reasoning = models.TextField(blank=True, help_text="Optional player reasoning")
    
    class Meta:
        verbose_name = "Climate Player Response"
        verbose_name_plural = "Climate Player Responses"
        ordering = ['-submitted_at']
        unique_together = ['climate_session', 'player_session_id', 'climate_scenario']
    
    def __str__(self):
        return f"{self.player_name} ({self.assigned_role}) - {self.climate_scenario.title}"
    
    def save(self, *args, **kwargs):
        """Auto-increment option selection count when response is saved"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.selected_option:
            self.selected_option.increment_selection()


class ClimateRoundResult(models.Model):
    """
    Aggregated results for each round of climate game
    Stores outcome calculations and narrative feedback
    """
    session = models.ForeignKey(ClimateGameSession, on_delete=models.CASCADE, related_name='round_results')
    scenario = models.ForeignKey(ClimateScenario, on_delete=models.CASCADE)
    
    # Aggregated Response Data
    response_summary = models.JSONField(
        default=dict,
        help_text="Percentage breakdown of choices by role"
    )
    
    # Calculated Outcomes
    meter_changes = models.JSONField(
        default=dict,
        help_text="How meters changed this round"
    )
    meters_after = models.JSONField(
        default=dict,
        help_text="Meter values after this round"
    )
    
    # Generated Narrative
    outcome_narrative = models.TextField(
        help_text="AI-generated or pre-written narrative about consequences"
    )
    learning_outcome = models.TextField(
        help_text="Key learning points from this round"
    )
    
    # Cross-role interactions
    collaboration_bonus = models.IntegerField(
        default=0,
        help_text="Bonus points for complementary choices across roles"
    )
    conflict_penalty = models.IntegerField(
        default=0,
        help_text="Penalty for contradictory choices"
    )
    
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Climate Round Result"
        verbose_name_plural = "Climate Round Results"
        ordering = ['-calculated_at']
        unique_together = ['session', 'scenario']
    
    def __str__(self):
        return f"{self.session.session_code} - {self.scenario.title} Results"


# ==================================================================================
# DESIGN THINKING / CLASSROOM INNOVATORS CHALLENGE MODELS
# ==================================================================================

class DesignThinkingGame(Game):
    """
    Design Thinking Game - "The Classroom Innovators Challenge"
    Extends base Game model for facilitator-controlled Design Thinking sessions
    """
    # Facilitator Control Settings
    auto_advance_missions = models.BooleanField(
        default=False,
        help_text="Automatically advance missions when all teams complete"
    )
    default_mission_duration = models.IntegerField(
        default=15,
        help_text="Default duration for each mission in minutes"
    )
    require_all_teams_complete = models.BooleanField(
        default=False,
        help_text="Require all teams to complete before advancing to next mission"
    )
    
    # Virtual Mentor (Vani) Configuration
    enable_mentor_prompts = models.BooleanField(
        default=True,
        help_text="Enable Vani (Virtual Mentor) prompts during gameplay"
    )
    mentor_prompt_frequency = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Minimal prompts'),
            ('medium', 'Regular prompts'),
            ('high', 'Frequent prompts')
        ],
        default='medium',
        help_text="How frequently Vani provides guidance"
    )
    
    class Meta:
        verbose_name = "Design Thinking Game"
        verbose_name_plural = "Design Thinking Games"


class DesignMission(models.Model):
    """
    Individual missions within the Design Thinking process
    (Kickoff, Empathy, Define, Ideate, Prototype)
    """
    MISSION_TYPES = [
        ('kickoff', 'Energizing Kickoff'),
        ('empathy', 'Empathy Mission'),
        ('define', 'Define Mission'),
        ('ideate', 'Ideate Mission'),
        ('prototype', 'Prototype Mission'),
        ('showcase', 'Final Showcase'),
    ]
    
    game = models.ForeignKey(DesignThinkingGame, on_delete=models.CASCADE, related_name='missions')
    mission_type = models.CharField(max_length=20, choices=MISSION_TYPES)
    order = models.PositiveIntegerField(help_text="Mission sequence order")
    
    # Mission Content
    title = models.CharField(max_length=200, help_text="Mission title")
    description = models.TextField(help_text="What students will do in this mission")
    instructions = models.TextField(help_text="Step-by-step instructions for teams")
    
    # Timing Configuration
    estimated_duration = models.IntegerField(
        default=15,
        help_text="Estimated duration in minutes"
    )
    minimum_time = models.IntegerField(
        default=5,
        help_text="Minimum time before mission can be advanced"
    )
    
    # Mission-Specific Configuration
    requires_file_upload = models.BooleanField(
        default=False,
        help_text="Teams must upload files/photos during this mission"
    )
    requires_text_submission = models.BooleanField(
        default=True,
        help_text="Teams must submit text responses"
    )
    max_submissions = models.IntegerField(
        default=1,
        help_text="Maximum submissions per team for this mission"
    )
    
    # Learning Objectives
    learning_focus = models.TextField(
        blank=True,
        help_text="What students will learn from this mission"
    )
    success_criteria = models.TextField(
        blank=True,
        help_text="How to measure mission success"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Design Mission"
        verbose_name_plural = "Design Missions"
        ordering = ['game', 'order']
        unique_together = ['game', 'order']
    
    def __str__(self):
        return f"{self.game.title} - {self.get_mission_type_display()}"


class DesignThinkingSession(GameSession):
    """
    Live Design Thinking session - extends base GameSession
    Tracks current mission, facilitator controls, and team progress
    """
    design_game = models.ForeignKey(DesignThinkingGame, on_delete=models.CASCADE, related_name='design_sessions')
    
    # Current Mission State
    current_mission = models.ForeignKey(
        DesignMission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Currently active mission"
    )
    mission_start_time = models.DateTimeField(null=True, blank=True)
    mission_end_time = models.DateTimeField(null=True, blank=True)
    
    # Facilitator Control State
    is_facilitator_controlled = models.BooleanField(
        default=True,
        help_text="Whether facilitator controls mission advancement"
    )
    facilitator_notes = models.TextField(
        blank=True,
        help_text="Private notes for the facilitator"
    )
    
    # Session Configuration
    enable_peer_viewing = models.BooleanField(
        default=True,
        help_text="Allow teams to see other teams' submissions"
    )
    enable_live_feedback = models.BooleanField(
        default=True,
        help_text="Enable real-time feedback and spotlighting"
    )
    
    # Virtual Mentor State
    mentor_active = models.BooleanField(
        default=True,
        help_text="Whether Vani mentor is currently active"
    )
    last_mentor_prompt = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Design Thinking Session"
        verbose_name_plural = "Design Thinking Sessions"
    
    def get_teams_count(self):
        """Get number of active teams in session"""
        return self.design_teams.count()
    
    def get_mission_progress(self):
        """Get overall mission progress for all teams"""
        if not self.current_mission:
            return {'completed': 0, 'total': 0, 'percentage': 0}
        
        total_teams = self.get_teams_count()
        completed_teams = TeamProgress.objects.filter(
            session=self,
            mission=self.current_mission,
            is_completed=True
        ).count()
        
        return {
            'completed': completed_teams,
            'total': total_teams,
            'percentage': (completed_teams / total_teams * 100) if total_teams > 0 else 0
        }
    
    def can_advance_mission(self):
        """Check if mission can be advanced based on completion criteria"""
        if not self.current_mission:
            return True
        
        if self.design_game.require_all_teams_complete:
            progress = self.get_mission_progress()
            return progress['percentage'] >= 100
        
        return True
    
    def complete_session(self):
        """Mark session as completed and expire it"""
        self.status = 'completed'
        self.save()
        
        # Set mission end time if current mission exists
        if self.current_mission and not self.mission_end_time:
            from django.utils import timezone
            self.mission_end_time = timezone.now()
            self.save()
    
    def is_expired(self):
        """Check if session has expired"""
        return self.status in ['completed', 'abandoned']
    
    def get_all_missions(self):
        """Get all missions for this design game in order"""
        return DesignMission.objects.filter(game=self.design_game).order_by('order')
    
    def is_final_mission(self):
        """Check if current mission is the final mission"""
        if not self.current_mission:
            return False
        
        all_missions = self.get_all_missions()
        return self.current_mission == all_missions.last()


class DesignTeam(models.Model):
    """
    Team participating in Design Thinking session
    """
    session = models.ForeignKey(DesignThinkingSession, on_delete=models.CASCADE, related_name='design_teams')
    
    # Team Identity
    team_name = models.CharField(max_length=100, help_text="Team's chosen name")
    team_emoji = models.CharField(
        max_length=10,
        default='💡',
        help_text="Team's chosen emoji"
    )
    team_color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text="Team's chosen color (hex code)"
    )
    
    # Team Members (stored as JSON for flexibility)
    team_members = models.JSONField(
        default=list,
        help_text="List of team member names and roles"
    )
    
    # Team Progress
    current_mission = models.ForeignKey(
        DesignMission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Team's current mission"
    )
    missions_completed = models.PositiveIntegerField(default=0)
    total_submissions = models.PositiveIntegerField(default=0)
    
    # Problem Focus (developed during Define mission)
    problem_statement = models.TextField(
        blank=True,
        help_text="Team's defined problem statement (POV)"
    )
    target_user = models.CharField(
        max_length=200,
        blank=True,
        help_text="Target user identified by team"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Design Team"
        verbose_name_plural = "Design Teams"
        ordering = ['team_name']
    
    def __str__(self):
        return f"{self.team_name} ({self.session.session_code})"
    
    def get_progress_percentage(self):
        """Calculate team's overall progress percentage based on actual completed missions"""
        total_missions = self.session.design_game.missions.filter(is_active=True).count()
        if total_missions == 0:
            return 0
        
        # Count actually completed missions from TeamProgress records
        completed_missions = self.mission_progress.filter(is_completed=True).count()
        return (completed_missions / total_missions) * 100


class TeamProgress(models.Model):
    """
    Track individual team progress through each mission
    """
    session = models.ForeignKey(DesignThinkingSession, on_delete=models.CASCADE, related_name='team_progress')
    team = models.ForeignKey(DesignTeam, on_delete=models.CASCADE, related_name='mission_progress')
    mission = models.ForeignKey(DesignMission, on_delete=models.CASCADE)
    
    # Progress Tracking
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    # Mission-Specific Data
    submission_count = models.PositiveIntegerField(default=0)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    
    # Facilitator Feedback
    facilitator_spotlight = models.BooleanField(
        default=False,
        help_text="Highlighted by facilitator for good work"
    )
    facilitator_notes = models.TextField(
        blank=True,
        help_text="Private facilitator notes about team's progress"
    )
    
    class Meta:
        verbose_name = "Team Progress"
        verbose_name_plural = "Team Progress Records"
        ordering = ['-started_at']
        unique_together = ['session', 'team', 'mission']
    
    def __str__(self):
        return f"{self.team.team_name} - {self.mission.get_mission_type_display()}"
    
    def mark_completed(self):
        """Mark mission as completed for this team"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
        
        # Update team's overall progress
        self.team.missions_completed = self.team.mission_progress.filter(is_completed=True).count()
        self.team.save()


class TeamSubmission(models.Model):
    """
    Individual submissions from teams during missions
    (observations, problem statements, ideas, prototypes)
    """
    SUBMISSION_TYPES = [
        ('observation', 'Empathy Observation'),
        ('photo', 'Photo Evidence'),
        ('voice_note', 'Voice Note'),
        ('problem_statement', 'Problem Statement (POV)'),
        ('idea', 'Generated Idea'),
        ('prototype_description', 'Prototype Description'),
        ('prototype_photo', 'Prototype Photo'),
        ('reflection', 'Mission Reflection'),
    ]
    
    team = models.ForeignKey(DesignTeam, on_delete=models.CASCADE, related_name='submissions')
    mission = models.ForeignKey(DesignMission, on_delete=models.CASCADE)
    submission_type = models.CharField(max_length=30, choices=SUBMISSION_TYPES)
    
    # Submission Content
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional title for submission"
    )
    content = models.TextField(help_text="Text content of submission")
    
    # File Attachments
    uploaded_file = models.FileField(
        upload_to='design_thinking_submissions/',
        blank=True,
        null=True,
        help_text="Uploaded photo, audio, or document"
    )
    file_type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('image', 'Image/Photo'),
            ('audio', 'Audio Recording'),
            ('document', 'Document'),
        ]
    )
    
    # Submission Metadata
    submitted_by = models.CharField(
        max_length=100,
        help_text="Name of team member who submitted"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Engagement Tracking
    view_count = models.PositiveIntegerField(default=0)
    peer_likes = models.PositiveIntegerField(default=0)
    facilitator_featured = models.BooleanField(
        default=False,
        help_text="Featured by facilitator during showcase"
    )
    
    # Mission-Specific Fields
    empathy_target_user = models.CharField(
        max_length=200,
        blank=True,
        help_text="Target user for empathy observation"
    )
    idea_category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Category for ideation submissions"
    )
    
    class Meta:
        verbose_name = "Team Submission"
        verbose_name_plural = "Team Submissions"
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.team.team_name} - {self.get_submission_type_display()}"
    
    def increment_view_count(self):
        """Track when submission is viewed"""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class MentorNudge(models.Model):
    """
    Virtual Mentor (Vani) prompts and guidance for teams
    """
    NUDGE_TRIGGERS = [
        ('mission_start', 'Mission Start'),
        ('time_based', 'Time-based'),
        ('progress_based', 'Progress-based'),
        ('facilitator_triggered', 'Facilitator Triggered'),
        ('team_specific', 'Team-specific'),
    ]
    
    NUDGE_TYPES = [
        ('encouragement', 'Encouragement'),
        ('instruction', 'Instruction/Guidance'),
        ('prompt', 'Thinking Prompt'),
        ('celebration', 'Celebration'),
        ('refocus', 'Refocus/Redirect'),
    ]
    
    mission = models.ForeignKey(DesignMission, on_delete=models.CASCADE, related_name='mentor_nudges')
    
    # Nudge Content
    title = models.CharField(max_length=200, help_text="Nudge title/header")
    message = models.TextField(help_text="Vani's message to teams")
    nudge_type = models.CharField(max_length=20, choices=NUDGE_TYPES)
    
    # Trigger Configuration
    trigger_type = models.CharField(max_length=25, choices=NUDGE_TRIGGERS)
    trigger_time_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Seconds after mission start to trigger (for time-based)"
    )
    trigger_condition = models.JSONField(
        default=dict,
        blank=True,
        help_text="Conditions for triggering this nudge"
    )
    
    # Display Configuration
    display_duration = models.PositiveIntegerField(
        default=10,
        help_text="How long to display nudge in seconds"
    )
    is_dismissible = models.BooleanField(
        default=True,
        help_text="Can teams dismiss this nudge"
    )
    
    # Visual Style
    emoji = models.CharField(
        max_length=10,
        default='💡',
        help_text="Emoji for Vani's expression"
    )
    background_color = models.CharField(
        max_length=7,
        default='#10B981',
        help_text="Background color for nudge (hex)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Mentor Nudge"
        verbose_name_plural = "Mentor Nudges"
        ordering = ['mission', 'trigger_time_seconds']
    
    def __str__(self):
        return f"{self.mission.get_mission_type_display()} - {self.title}"
