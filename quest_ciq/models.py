from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Quest(models.Model):
    """Represents a CIQ Quest with multiple levels"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    slug = models.SlugField(unique=True, max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    max_participants = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Quest"
        verbose_name_plural = "Quests"

    def __str__(self):
        return self.title


class QuestLevel(models.Model):
    """Individual levels within a quest"""
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='levels')
    level_number = models.IntegerField(validators=[MinValueValidator(1)])
    title = models.CharField(max_length=200)
    description = models.TextField()
    question_text = models.TextField()
    max_score = models.IntegerField(default=100, validators=[MinValueValidator(0)])
    time_limit_minutes = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['quest', 'level_number']
        unique_together = ['quest', 'level_number']
        verbose_name = "Quest Level"
        verbose_name_plural = "Quest Levels"

    def __str__(self):
        return f"{self.quest.title} - Level {self.level_number}: {self.title}"


class Participant(models.Model):
    """Participant in a quest (can be student or teacher)"""
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    display_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    join_code = models.CharField(max_length=20, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Participant"
        verbose_name_plural = "Participants"

    def __str__(self):
        return f"{self.display_name} ({self.role})"


class QuestSession(models.Model):
    """A session where a participant attempts a quest"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='sessions')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='quest_sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_score = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    current_level = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['-started_at']
        unique_together = ['quest', 'participant']
        verbose_name = "Quest Session"
        verbose_name_plural = "Quest Sessions"

    def __str__(self):
        return f"{self.participant.display_name} - {self.quest.title} ({self.status})"

    def start_session(self):
        """Start the quest session"""
        if self.status == 'not_started':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.save()

    def complete_session(self):
        """Complete the quest session"""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()


class LevelResponse(models.Model):
    """Participant's response to a level"""
    session = models.ForeignKey(QuestSession, on_delete=models.CASCADE, related_name='level_responses')
    level = models.ForeignKey(QuestLevel, on_delete=models.CASCADE, related_name='responses')
    response_text = models.TextField()
    score = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    time_taken_seconds = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ['submitted_at']
        unique_together = ['session', 'level']
        verbose_name = "Level Response"
        verbose_name_plural = "Level Responses"

    def __str__(self):
        return f"{self.session.participant.display_name} - {self.level.title} (Score: {self.score})"


class Leaderboard(models.Model):
    """Cached leaderboard entries for performance"""
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='leaderboard_entries')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='leaderboard_entries')
    rank = models.IntegerField(validators=[MinValueValidator(1)])
    total_score = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    completion_time_seconds = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['quest', 'rank']
        unique_together = ['quest', 'participant']
        verbose_name = "Leaderboard Entry"
        verbose_name_plural = "Leaderboard Entries"

    def __str__(self):
        return f"#{self.rank} {self.participant.display_name} - {self.quest.title} ({self.total_score})"
