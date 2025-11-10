"""
Admin interface for Classroom Innovation Quest
"""
from django.contrib import admin
from .models import (
    Quest, ClassRoom, Team, QuestSession, QuestLevel,
    LevelResponse, PeerFeedback, TeacherTeamScore, CIQSettings
)


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_code', 'quest', 'teacher', 'is_active', 'created_at']
    list_filter = ['is_active', 'quest', 'created_at']
    search_fields = ['name', 'class_code', 'teacher__username']
    readonly_fields = ['class_code', 'created_at']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'classroom', 'created_at']
    list_filter = ['classroom', 'created_at']
    search_fields = ['name', 'slug', 'classroom__name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(QuestSession)
class QuestSessionAdmin(admin.ModelAdmin):
    list_display = ['session_code', 'student_name', 'team', 'classroom', 'current_level', 'total_score', 'created_at', 'completed_at']
    list_filter = ['current_level', 'completed_at', 'created_at', 'team', 'classroom']
    search_fields = ['session_code', 'student_name', 'team__name', 'classroom__name']
    readonly_fields = ['session_code', 'created_at', 'updated_at']
    ordering = ['-total_score', '-created_at']


@admin.register(QuestLevel)
class QuestLevelAdmin(admin.ModelAdmin):
    list_display = ['order', 'name', 'tooltip']
    ordering = ['order']


@admin.register(LevelResponse)
class LevelResponseAdmin(admin.ModelAdmin):
    list_display = ['session', 'level_order', 'submitted_at']
    list_filter = ['level_order', 'submitted_at']
    search_fields = ['session__student_name', 'session__session_code']
    readonly_fields = ['submitted_at']


@admin.register(PeerFeedback)
class PeerFeedbackAdmin(admin.ModelAdmin):
    list_display = ['session', 'peer_name', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['session__student_name', 'peer_name']


@admin.register(TeacherTeamScore)
class TeacherTeamScoreAdmin(admin.ModelAdmin):
    list_display = ['team', 'classroom', 'quest', 'score', 'graded_by', 'graded_at']
    list_filter = ['quest', 'classroom', 'graded_at']
    search_fields = ['team__name', 'classroom__name', 'quest__name']
    readonly_fields = ['graded_at', 'created_at']
    ordering = ['-graded_at']


@admin.register(CIQSettings)
class CIQSettingsAdmin(admin.ModelAdmin):
    list_display = ['enable_ciq', 'show_leaderboard', 'max_file_size_mb']

    def has_add_permission(self, request):
        # Only allow one settings object
        return not CIQSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False
