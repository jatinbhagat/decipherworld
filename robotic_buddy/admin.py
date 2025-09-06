from django.contrib import admin
from .models import RoboticBuddy, GameActivity, TrainingSession, TrainingExample, BuddyAchievement


@admin.register(RoboticBuddy)
class RoboticBuddyAdmin(admin.ModelAdmin):
    list_display = ['name', 'personality', 'current_level', 'experience_points', 'total_training_sessions', 'created_at', 'last_active']
    list_filter = ['personality', 'current_level', 'created_at']
    search_fields = ['name', 'session_id']
    readonly_fields = ['session_id', 'created_at', 'last_active']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'session_id', 'created_at', 'last_active')
        }),
        ('Customization', {
            'fields': ('personality', 'primary_color', 'secondary_color')
        }),
        ('Progress', {
            'fields': ('current_level', 'experience_points', 'total_training_sessions', 'total_examples_learned')
        }),
        ('Knowledge Base', {
            'fields': ('knowledge_base',),
            'classes': ('collapse',)
        })
    )


@admin.register(GameActivity)
class GameActivityAdmin(admin.ModelAdmin):
    list_display = ['name', 'activity_type', 'difficulty_level', 'required_level', 'experience_reward', 'is_active']
    list_filter = ['activity_type', 'difficulty_level', 'required_level', 'is_active']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'activity_type', 'difficulty_level', 'description', 'instructions')
        }),
        ('Game Configuration', {
            'fields': ('min_examples_needed', 'max_examples', 'experience_reward')
        }),
        ('Requirements', {
            'fields': ('required_level', 'is_active')
        })
    )


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ['buddy', 'activity', 'status', 'examples_provided', 'accuracy', 'experience_earned', 'started_at']
    list_filter = ['status', 'activity__activity_type', 'started_at']
    search_fields = ['buddy__name', 'activity__name']
    readonly_fields = ['started_at', 'completed_at', 'accuracy', 'duration_minutes']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('buddy', 'activity', 'status', 'started_at', 'completed_at', 'duration_minutes')
        }),
        ('Results', {
            'fields': ('examples_provided', 'correct_predictions', 'total_predictions', 'accuracy', 'experience_earned')
        }),
        ('Session Data', {
            'fields': ('session_data',),
            'classes': ('collapse',)
        })
    )


@admin.register(TrainingExample)
class TrainingExampleAdmin(admin.ModelAdmin):
    list_display = ['session', 'example_type', 'label', 'buddy_prediction', 'was_correct', 'confidence_level', 'created_at']
    list_filter = ['example_type', 'was_correct', 'session__activity__activity_type']
    search_fields = ['label', 'buddy_prediction', 'session__buddy__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Example Info', {
            'fields': ('session', 'example_type', 'label', 'created_at')
        }),
        ('Buddy Response', {
            'fields': ('buddy_prediction', 'was_correct', 'confidence_level')
        }),
        ('Example Data', {
            'fields': ('data',),
            'classes': ('collapse',)
        })
    )


@admin.register(BuddyAchievement)
class BuddyAchievementAdmin(admin.ModelAdmin):
    list_display = ['buddy', 'name', 'achievement_type', 'unlocked_at']
    list_filter = ['achievement_type', 'unlocked_at']
    search_fields = ['buddy__name', 'name', 'description']
    readonly_fields = ['unlocked_at']
