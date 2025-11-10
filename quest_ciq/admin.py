from django.contrib import admin
from django.utils.html import format_html
from .models import Quest, QuestLevel, Participant, QuestSession, LevelResponse, Leaderboard


class QuestLevelInline(admin.TabularInline):
    """Inline admin for quest levels"""
    model = QuestLevel
    extra = 1
    fields = ('level_number', 'title', 'max_score', 'time_limit_minutes')


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    """Admin for Quest model"""
    list_display = ('title', 'slug', 'is_active', 'max_participants', 'created_at', 'level_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [QuestLevelInline]
    date_hierarchy = 'created_at'

    def level_count(self, obj):
        """Display number of levels"""
        return obj.levels.count()
    level_count.short_description = 'Levels'


@admin.register(QuestLevel)
class QuestLevelAdmin(admin.ModelAdmin):
    """Admin for QuestLevel model"""
    list_display = ('quest', 'level_number', 'title', 'max_score', 'time_limit_minutes')
    list_filter = ('quest',)
    search_fields = ('title', 'question_text', 'quest__title')
    ordering = ('quest', 'level_number')


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    """Admin for Participant model"""
    list_display = ('display_name', 'email', 'role', 'join_code', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('display_name', 'email', 'join_code')
    readonly_fields = ('join_code', 'created_at')
    date_hierarchy = 'created_at'


class LevelResponseInline(admin.TabularInline):
    """Inline admin for level responses"""
    model = LevelResponse
    extra = 0
    readonly_fields = ('level', 'score', 'submitted_at')
    fields = ('level', 'response_text', 'score', 'feedback', 'submitted_at')
    can_delete = False


@admin.register(QuestSession)
class QuestSessionAdmin(admin.ModelAdmin):
    """Admin for QuestSession model"""
    list_display = ('participant', 'quest', 'status', 'current_level', 'total_score', 'started_at', 'completed_at')
    list_filter = ('status', 'quest', 'started_at', 'completed_at')
    search_fields = ('participant__display_name', 'quest__title')
    readonly_fields = ('started_at', 'completed_at')
    inlines = [LevelResponseInline]
    date_hierarchy = 'started_at'

    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('participant', 'quest')


@admin.register(LevelResponse)
class LevelResponseAdmin(admin.ModelAdmin):
    """Admin for LevelResponse model"""
    list_display = ('participant_name', 'level', 'score', 'submitted_at', 'time_taken_display')
    list_filter = ('level__quest', 'submitted_at')
    search_fields = ('session__participant__display_name', 'level__title', 'response_text')
    readonly_fields = ('submitted_at',)
    date_hierarchy = 'submitted_at'

    def participant_name(self, obj):
        """Display participant name"""
        return obj.session.participant.display_name
    participant_name.short_description = 'Participant'

    def time_taken_display(self, obj):
        """Display time taken in readable format"""
        if obj.time_taken_seconds:
            minutes = obj.time_taken_seconds // 60
            seconds = obj.time_taken_seconds % 60
            return f"{minutes}m {seconds}s"
        return "-"
    time_taken_display.short_description = 'Time Taken'

    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('session__participant', 'level')


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    """Admin for Leaderboard model"""
    list_display = ('rank', 'participant', 'quest', 'total_score', 'completion_time_display', 'updated_at')
    list_filter = ('quest', 'updated_at')
    search_fields = ('participant__display_name', 'quest__title')
    readonly_fields = ('rank', 'updated_at')
    ordering = ('quest', 'rank')

    def completion_time_display(self, obj):
        """Display completion time in readable format"""
        if obj.completion_time_seconds:
            hours = obj.completion_time_seconds // 3600
            minutes = (obj.completion_time_seconds % 3600) // 60
            seconds = obj.completion_time_seconds % 60

            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "-"
    completion_time_display.short_description = 'Completion Time'

    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('participant', 'quest')


# Customize admin site header
admin.site.site_header = "Quest CIQ Administration"
admin.site.site_title = "Quest CIQ Admin"
admin.site.index_title = "Welcome to Quest CIQ Administration"
