from django.contrib import admin
from .models import Quest, QuestLevel, Participant, QuestSession, LevelResponse, Leaderboard


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'slug', 'description']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(QuestLevel)
class QuestLevelAdmin(admin.ModelAdmin):
    list_display = ['quest', 'order', 'name', 'short_help']
    list_filter = ['quest']
    search_fields = ['name', 'short_help']
    ordering = ['quest', 'order']


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'quest', 'joined_at', 'is_active']
    list_filter = ['quest', 'is_active', 'joined_at']
    search_fields = ['user__username', 'user__email', 'quest__title']
    date_hierarchy = 'joined_at'


@admin.register(QuestSession)
class QuestSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'participant', 'quest', 'started_at', 'total_score', 'is_frozen', 'completed_at']
    list_filter = ['quest', 'is_frozen', 'started_at']
    search_fields = ['participant__user__username', 'quest__title']
    date_hierarchy = 'started_at'
    readonly_fields = ['started_at', 'total_score']


@admin.register(LevelResponse)
class LevelResponseAdmin(admin.ModelAdmin):
    list_display = ['session', 'level', 'score', 'submitted_at']
    list_filter = ['level__quest', 'level', 'submitted_at']
    search_fields = ['session__participant__user__username', 'level__name']
    date_hierarchy = 'submitted_at'
    readonly_fields = ['submitted_at', 'updated_at']


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['rank', 'participant', 'quest', 'total_score', 'levels_completed', 'last_updated']
    list_filter = ['quest', 'last_updated']
    search_fields = ['participant__user__username', 'quest__title']
    ordering = ['quest', 'rank']
    readonly_fields = ['last_updated']
