"""
Models for Classroom Innovation Quest (CIQ)
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class Quest(models.Model):
    """
    A quest (e.g., 'Classroom Innovation Quest') with multiple levels.
    """
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quest'
        verbose_name_plural = 'Quests'

    def __str__(self):
        return self.title


class QuestLevel(models.Model):
    """
    A level within a quest (e.g., Empathy, Define, Ideate, Prototype, Test).
    """
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='levels')
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=100)
    short_help = models.TextField(blank=True)
    schema = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON schema describing expected fields for this level"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['quest', 'order']
        unique_together = ['quest', 'order']
        verbose_name = 'Quest Level'
        verbose_name_plural = 'Quest Levels'

    def __str__(self):
        return f"{self.quest.title} - Level {self.order}: {self.name}"


class Participant(models.Model):
    """
    A user participating in quests. Links user to their quest activities.
    Can be anonymous (user=None) or authenticated.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quest_participations', null=True, blank=True)
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='participants')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-joined_at']
        verbose_name = 'Participant'
        verbose_name_plural = 'Participants'

    def __str__(self):
        username = self.user.username if self.user else f"Anonymous-{self.id}"
        return f"{username} in {self.quest.title}"


class QuestSession(models.Model):
    """
    A session representing a user's journey through a quest.
    """
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='sessions')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_frozen = models.BooleanField(
        default=False,
        help_text="If true, user cannot submit new responses"
    )
    total_score = models.IntegerField(default=0)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Quest Session'
        verbose_name_plural = 'Quest Sessions'

    def __str__(self):
        username = self.participant.user.username if self.participant.user else f"Anonymous-{self.participant.id}"
        return f"Session #{self.pk} - {username} in {self.quest.title}"

    def get_highest_completed_level(self):
        """Get the highest level order number that has been completed."""
        highest = self.responses.aggregate(models.Max('level__order'))
        return highest['level__order__max'] or 0

    def can_access_level(self, level_order):
        """Check if user can access a given level based on gating logic."""
        if level_order == 1:
            return True  # Level 1 is always accessible

        # Check if previous level is completed
        previous_level_completed = self.responses.filter(
            level__order=level_order - 1
        ).exists()

        return previous_level_completed

    def update_total_score(self):
        """Recalculate and update total score from all level responses."""
        total = self.responses.aggregate(models.Sum('score'))
        self.total_score = total['score__sum'] or 0
        self.save(update_fields=['total_score'])


class LevelResponse(models.Model):
    """
    A user's response/submission for a specific quest level.
    """
    session = models.ForeignKey(QuestSession, on_delete=models.CASCADE, related_name='responses')
    level = models.ForeignKey(QuestLevel, on_delete=models.CASCADE, related_name='responses')
    answers = models.JSONField(
        default=dict,
        help_text="JSON field storing form responses for this level"
    )
    score = models.IntegerField(default=0)
    prototype_upload = models.ImageField(
        upload_to='quest_prototypes/',
        null=True,
        blank=True,
        help_text="Optional prototype image upload (max 2MB)"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['session', 'level__order']
        unique_together = ['session', 'level']
        verbose_name = 'Level Response'
        verbose_name_plural = 'Level Responses'

    def __str__(self):
        username = self.session.participant.user.username if self.session.participant.user else f"Anonymous-{self.session.participant.id}"
        return f"{username} - {self.level.name} (Score: {self.score})"

    def calculate_score(self):
        """
        Calculate score based on level-specific rules.
        Base: +10 points per level
        Bonuses:
        - L3 (Ideate): +10 if ideas_list >= 120 chars or >= 2 items
        - L4 (Prototype): +10 if prototype_link or prototype_upload provided
        - L5 (Test): +10 if peer_rating >= 4
        """
        from quest_ciq.services.scoring import calculate_level_score
        self.score = calculate_level_score(self)
        return self.score


class Leaderboard(models.Model):
    """
    Cached leaderboard entries for a quest.
    """
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='leaderboard_entries')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='leaderboard_entries')
    rank = models.PositiveIntegerField(default=0)
    total_score = models.IntegerField(default=0)
    levels_completed = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['quest', 'rank']
        unique_together = ['quest', 'participant']
        verbose_name = 'Leaderboard Entry'
        verbose_name_plural = 'Leaderboard Entries'

    def __str__(self):
        username = self.participant.user.username if self.participant.user else f"Anonymous-{self.participant.id}"
        return f"#{self.rank} - {username} in {self.quest.title} ({self.total_score} pts)"

    @classmethod
    def refresh_for_quest(cls, quest):
        """
        Refresh leaderboard rankings for a quest.
        """
        from django.db.models import Count, Sum

        # Get all participants with their scores
        participants_data = []
        for participant in quest.participants.filter(is_active=True):
            sessions = participant.sessions.filter(quest=quest)
            total_score = sessions.aggregate(Sum('total_score'))['total_score__sum'] or 0

            # Count unique levels completed across all sessions
            levels_completed = LevelResponse.objects.filter(
                session__participant=participant,
                session__quest=quest
            ).values('level').distinct().count()

            participants_data.append({
                'participant': participant,
                'total_score': total_score,
                'levels_completed': levels_completed
            })

        # Sort by score (desc), then by levels completed (desc)
        participants_data.sort(key=lambda x: (-x['total_score'], -x['levels_completed']))

        # Update or create leaderboard entries
        for rank, data in enumerate(participants_data, start=1):
            cls.objects.update_or_create(
                quest=quest,
                participant=data['participant'],
                defaults={
                    'rank': rank,
                    'total_score': data['total_score'],
                    'levels_completed': data['levels_completed']
                }
            )
