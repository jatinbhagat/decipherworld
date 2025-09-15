from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class RoboticBuddy(models.Model):
    """
    Main model representing a child's personalized Robotic Buddy
    """
    PERSONALITY_CHOICES = [
        ('cheerful', 'Cheerful & Energetic'),
        ('curious', 'Curious & Inquisitive'), 
        ('patient', 'Patient & Thoughtful'),
        ('playful', 'Playful & Fun-loving'),
        ('wise', 'Wise & Encouraging'),
    ]
    
    COLOR_CHOICES = [
        ('blue', 'Ocean Blue'),
        ('green', 'Forest Green'),
        ('purple', 'Royal Purple'),
        ('orange', 'Sunset Orange'),
        ('pink', 'Bubblegum Pink'),
        ('red', 'Fire Red'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=50, help_text="Buddy's name chosen by the child")
    session_id = models.CharField(max_length=100, unique=True, help_text="Anonymous session identifier")
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    
    # Customization
    personality = models.CharField(max_length=20, choices=PERSONALITY_CHOICES, default='cheerful')
    primary_color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='blue')
    secondary_color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='green')
    
    # Learning Progress
    total_training_sessions = models.IntegerField(default=0)
    total_examples_learned = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1, help_text="Buddy's learning level")
    experience_points = models.IntegerField(default=0)
    
    # AI "Brain" - Simulated learning data
    knowledge_base = models.JSONField(
        default=dict,
        help_text="Stores what the buddy has 'learned' from training sessions"
    )
    
    class Meta:
        verbose_name = "Robotic Buddy"
        verbose_name_plural = "Robotic Buddies"
        ordering = ['-last_active']
    
    def __str__(self):
        return f"{self.name} (Level {self.current_level})"
    
    def add_experience(self, points):
        """Add experience points and level up if needed"""
        self.experience_points += points
        new_level = min(10, (self.experience_points // 100) + 1)  # Max level 10
        if new_level > self.current_level:
            self.current_level = new_level
        self.save()
    
    def get_personality_greeting(self):
        """Get a greeting message based on personality"""
        greetings = {
            'cheerful': "Hi there! I'm so excited to learn with you today! 🌟",
            'curious': "Hello! I wonder what amazing things you'll teach me today? 🤔",
            'patient': "Welcome back, friend. I'm ready to learn at your pace. 😊",
            'playful': "Hey buddy! Ready for some fun learning games? 🎮",
            'wise': "Greetings, young learner. Together we shall discover new knowledge. 🦉",
        }
        return greetings.get(self.personality, greetings['cheerful'])


class GameActivity(models.Model):
    """
    Different types of training activities available in the game
    """
    ACTIVITY_TYPES = [
        ('classification', 'Object Classification'),
        ('command_training', 'Command Training'),
        ('emotion_detection', 'Emotion Recognition'),
        ('decision_tree', 'Decision Tree Logic'),
        ('pattern_recognition', 'Pattern Recognition'),
    ]
    
    DIFFICULTY_LEVELS = [
        (1, 'Beginner'),
        (2, 'Intermediate'), 
        (3, 'Advanced'),
    ]
    
    name = models.CharField(max_length=100)
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    difficulty_level = models.IntegerField(choices=DIFFICULTY_LEVELS, default=1)
    description = models.TextField(help_text="Kid-friendly description of the activity")
    instructions = models.TextField(help_text="How to play instructions")
    
    # Game Configuration
    min_examples_needed = models.IntegerField(default=16, help_text="Minimum examples needed to 'train' buddy")
    max_examples = models.IntegerField(default=16, help_text="Maximum examples in one session")
    experience_reward = models.IntegerField(default=10, help_text="XP awarded for completing activity")
    
    # Prerequisites
    required_level = models.IntegerField(default=1, help_text="Buddy level required to unlock")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Game Activity"
        verbose_name_plural = "Game Activities"
        ordering = ['required_level', 'difficulty_level', 'name']
    
    def __str__(self):
        return f"{self.name} (Level {self.required_level}+)"


class TrainingSession(models.Model):
    """
    Records of individual training sessions between child and buddy
    """
    STATUS_CHOICES = [
        ('training', 'Training Phase'),
        ('testing', 'Testing Phase'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    buddy = models.ForeignKey(RoboticBuddy, on_delete=models.CASCADE, related_name='training_sessions')
    activity = models.ForeignKey(GameActivity, on_delete=models.CASCADE, related_name='sessions')
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    training_completed_at = models.DateTimeField(null=True, blank=True, help_text="When training phase completed")
    testing_started_at = models.DateTimeField(null=True, blank=True, help_text="When testing phase started")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='training')
    
    # Session Results
    examples_provided = models.IntegerField(default=0)
    correct_predictions = models.IntegerField(default=0)
    total_predictions = models.IntegerField(default=0) 
    experience_earned = models.IntegerField(default=0)
    
    # Session Data
    session_data = models.JSONField(
        default=dict,
        help_text="Stores detailed session information and examples"
    )
    
    class Meta:
        verbose_name = "Training Session"
        verbose_name_plural = "Training Sessions"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.buddy.name} - {self.activity.name} ({self.status})"
    
    def complete_session(self):
        """Mark session as completed and award experience"""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.completed_at = timezone.now()
            
            # Calculate experience based on performance
            base_xp = self.activity.experience_reward
            performance_bonus = 0
            if self.total_predictions > 0:
                accuracy = self.correct_predictions / self.total_predictions
                performance_bonus = int(base_xp * accuracy * 0.5)  # Up to 50% bonus
            
            self.experience_earned = base_xp + performance_bonus
            
            # Update buddy stats
            self.buddy.total_training_sessions += 1
            self.buddy.total_examples_learned += self.examples_provided
            self.buddy.add_experience(self.experience_earned)
            
            self.save()
    
    @property
    def accuracy(self):
        """Calculate prediction accuracy as percentage"""
        if self.total_predictions == 0:
            return 0
        return round((self.correct_predictions / self.total_predictions) * 100, 1)
    
    @property
    def duration_minutes(self):
        """Calculate session duration in minutes"""
        if not self.completed_at:
            return 0
        delta = self.completed_at - self.started_at
        return round(delta.total_seconds() / 60, 1)


class TrainingExample(models.Model):
    """
    Individual examples provided during training sessions
    """
    EXAMPLE_TYPES = [
        ('classification_item', 'Classification Item'),
        ('command', 'Voice/Text Command'),
        ('emotion_image', 'Emotion Image'),
        ('pattern', 'Visual Pattern'),
    ]
    
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='examples')
    example_type = models.CharField(max_length=30, choices=EXAMPLE_TYPES)
    
    # Example Data
    label = models.CharField(max_length=100, help_text="What the example represents (e.g., 'cat', 'happy', 'jump')")
    data = models.JSONField(help_text="Example-specific data (image path, text, coordinates, etc.)")
    is_training_example = models.BooleanField(default=True, help_text="True for training phase, False for testing phase")
    
    # Buddy's Response
    buddy_prediction = models.CharField(max_length=100, blank=True, help_text="What buddy predicted")
    was_correct = models.BooleanField(default=False)
    confidence_level = models.FloatField(default=0.5, help_text="Simulated confidence (0.0-1.0)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Training Example"
        verbose_name_plural = "Training Examples"
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.label} -> {self.buddy_prediction or 'No prediction'} ({'✓' if self.was_correct else '✗'})"


class BuddyAchievement(models.Model):
    """
    Achievements and milestones for buddies to unlock
    """
    ACHIEVEMENT_TYPES = [
        ('first_steps', 'First Steps'),
        ('learning_streak', 'Learning Streak'),
        ('master_classifier', 'Master Classifier'),
        ('command_expert', 'Command Expert'),
        ('emotion_reader', 'Emotion Reader'),
        ('pattern_detective', 'Pattern Detective'),
    ]
    
    buddy = models.ForeignKey(RoboticBuddy, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=30, choices=ACHIEVEMENT_TYPES)
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Achievement Criteria
    required_sessions = models.IntegerField(default=0)
    required_examples = models.IntegerField(default=0) 
    required_accuracy = models.FloatField(default=0.0)
    
    unlocked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Buddy Achievement"
        verbose_name_plural = "Buddy Achievements"
        unique_together = ['buddy', 'achievement_type']
        ordering = ['-unlocked_at']
    
    def __str__(self):
        return f"{self.buddy.name} - {self.name}"


class AIReasoningExplanation(models.Model):
    """
    Detailed explanations of how the AI buddy made predictions
    """
    REASONING_TYPES = [
        ('pattern_matching', 'Pattern Matching'),
        ('similarity_comparison', 'Similarity Comparison'),
        ('feature_analysis', 'Feature Analysis'),
        ('example_based', 'Example-Based Learning'),
    ]
    
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='explanations')
    example = models.ForeignKey(TrainingExample, on_delete=models.CASCADE, related_name='reasoning')
    
    # Reasoning Details
    reasoning_type = models.CharField(max_length=30, choices=REASONING_TYPES, default='example_based')
    confidence_score = models.FloatField(help_text="AI confidence level (0.0-1.0)")
    confidence_explanation = models.TextField(help_text="Why this confidence level")
    
    # Step-by-step reasoning
    reasoning_steps = models.JSONField(
        default=list,
        help_text="Array of reasoning steps with descriptions and supporting examples"
    )
    
    # Supporting evidence
    supporting_examples = models.JSONField(
        default=list,
        help_text="Training examples that influenced this prediction"
    )
    
    # Visual patterns identified
    visual_patterns = models.JSONField(
        default=dict,
        help_text="Visual features or patterns the AI identified"
    )
    
    # Training quality impact
    training_quality_score = models.FloatField(default=1.0, help_text="Quality of training data that led to this prediction")
    quality_explanation = models.TextField(blank=True, help_text="How training quality affected this prediction")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "AI Reasoning Explanation"
        verbose_name_plural = "AI Reasoning Explanations"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reasoning for {self.example.label} - {self.confidence_score:.1%} confidence"
