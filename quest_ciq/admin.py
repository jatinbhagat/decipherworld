"""
Admin interface for Classroom Innovation Quest
"""
from django.contrib import admin
from .models import QuestSession, QuestLevel, LevelResponse, PeerFeedback, CIQSettings


@admin.register(QuestSession)
class QuestSessionAdmin(admin.ModelAdmin):
    list_display = ['session_code', 'student_name', 'current_level', 'total_score', 'created_at', 'completed_at']
    list_filter = ['current_level', 'completed_at', 'created_at']
    search_fields = ['session_code', 'student_name']
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


@admin.register(CIQSettings)
class CIQSettingsAdmin(admin.ModelAdmin):
    list_display = ['enable_ciq', 'show_leaderboard', 'max_file_size_mb']

    def has_add_permission(self, request):
        # Only allow one settings object
        return not CIQSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False
