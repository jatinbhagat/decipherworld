"""
Models for Classroom Innovation Quest
Session-based design thinking quest with 5 levels
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
import json
import random
import string


def generate_session_code():
    """Generate a unique 6-character session code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class QuestSession(models.Model):
    """
    Session for a Classroom Innovation Quest
    No authentication - session-based access for students
    """
    session_code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_session_code,
        help_text="Unique code students use to join"
    )
    student_name = models.CharField(
        max_length=100,
        help_text="Student's name"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Current progress
    current_level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Current level (1-5)"
    )

    # Scoring
    total_score = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_code']),
            models.Index(fields=['-total_score']),
        ]

    def __str__(self):
        return f"{self.student_name} ({self.session_code})"

    def save(self, *args, **kwargs):
        # Ensure unique session code
        while not self.session_code or QuestSession.objects.filter(session_code=self.session_code).exclude(pk=self.pk).exists():
            self.session_code = generate_session_code()
        super().save(*args, **kwargs)

    def calculate_score(self):
        """Calculate total score based on all level responses"""
        from .constants import SCORING

        score = 0
        responses = self.responses.all()

        for response in responses:
            # Base score per level
            score += SCORING['base_per_level']

            # Level-specific bonuses
            if response.level_order == 3:  # Ideate
                answers = response.get_answers()
                ideas = answers.get('ideas', [])
                non_empty_ideas = [i for i in ideas if i.strip()]
                total_chars = sum(len(i) for i in non_empty_ideas)

                if len(non_empty_ideas) >= 2:
                    score += SCORING['l3_bonus_ideas']
                if total_chars >= 120:
                    score += SCORING['l3_bonus_chars']

            elif response.level_order == 4:  # Prototype
                answers = response.get_answers()
                if answers.get('prototype_link') or answers.get('prototype_upload'):
                    score += SCORING['l4_bonus_upload']

            elif response.level_order == 5:  # Test
                answers = response.get_answers()
                if answers.get('peer_rating', 0) >= 4:
                    score += SCORING['l5_bonus_rating']

        self.total_score = score
        self.save(update_fields=['total_score'])
        return score

    def is_level_accessible(self, level_order):
        """Check if a level is accessible (previous level completed)"""
        if level_order == 1:
            return True
        return self.responses.filter(level_order=level_order - 1).exists()

    def advance_to_next_level(self):
        """Move to the next level"""
        if self.current_level < 5:
            self.current_level += 1
            self.save(update_fields=['current_level'])

        if self.current_level == 5 and not self.completed_at:
            # Check if all levels completed
            if self.responses.count() >= 5:
                self.completed_at = timezone.now()
                self.save(update_fields=['completed_at'])


class QuestLevel(models.Model):
    """
    Configuration for each quest level
    """
    order = models.IntegerField(
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Level order (1=Empathy, 2=Define, 3=Ideate, 4=Prototype, 5=Test)"
    )
    name = models.CharField(max_length=50)
    description = models.TextField(help_text="Instructions for students")
    tooltip = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Level {self.order}: {self.name}"


class LevelResponse(models.Model):
    """
    Student's response for a specific level
    """
    session = models.ForeignKey(
        QuestSession,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    level_order = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    answers = models.JSONField(
        default=dict,
        help_text="JSON structure of answers (varies by level)"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['session', 'level_order']
        ordering = ['level_order']
        indexes = [
            models.Index(fields=['session', 'level_order']),
        ]

    def __str__(self):
        return f"{self.session.student_name} - Level {self.level_order}"

    def get_answers(self):
        """Safely get answers dict"""
        if isinstance(self.answers, dict):
            return self.answers
        if isinstance(self.answers, str):
            try:
                return json.loads(self.answers)
            except:
                return {}
        return {}

    def clean(self):
        """Validate answers structure based on level"""
        answers = self.get_answers()

        if self.level_order == 1:  # Empathy
            if not answers.get('prioritized', {}).get('top'):
                raise ValidationError("Top priority pain point is required")

        elif self.level_order == 2:  # Define
            if not answers.get('hmw_goal') or not answers.get('hmw_outcome'):
                raise ValidationError("Both HMW goal and outcome are required")

        elif self.level_order == 3:  # Ideate
            ideas = answers.get('ideas', [])
            non_empty = [i for i in ideas if i.strip()]
            if len(non_empty) < 2:
                raise ValidationError("At least 2 ideas are required")

        elif self.level_order == 4:  # Prototype
            if 'selected_idea_index' not in answers:
                raise ValidationError("Selected idea is required")

        elif self.level_order == 5:  # Test
            if not answers.get('peer_rating'):
                raise ValidationError("Peer rating is required")


class PeerFeedback(models.Model):
    """
    Optional peer feedback model (for future extensions)
    """
    session = models.ForeignKey(
        QuestSession,
        on_delete=models.CASCADE,
        related_name='peer_feedbacks'
    )
    peer_name = models.CharField(max_length=100)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.peer_name} to {self.session.student_name}"


# Feature flag for enabling/disabling CIQ
class CIQSettings(models.Model):
    """
    Global settings for Classroom Innovation Quest
    """
    enable_ciq = models.BooleanField(
        default=True,
        help_text="Enable Classroom Innovation Quest feature"
    )
    max_file_size_mb = models.IntegerField(
        default=2,
        help_text="Maximum file upload size in MB"
    )
    show_leaderboard = models.BooleanField(
        default=True,
        help_text="Show public leaderboard"
    )

    class Meta:
        verbose_name = "CIQ Settings"
        verbose_name_plural = "CIQ Settings"

    def __str__(self):
        return "CIQ Settings"

    def save(self, *args, **kwargs):
        # Ensure only one settings object exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create singleton settings object"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
