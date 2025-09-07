from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    LearningModule, LearningObjective, Game, Role, Scenario, 
    Action, Outcome, GameSession, PlayerAction, ReflectionResponse
)


# Learning Content Admin

@admin.register(LearningModule)
class LearningModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'module_type', 'grade_level', 'is_active', 'created_at']
    list_filter = ['module_type', 'grade_level', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['module_type', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'module_type', 'grade_level')
        }),
        ('Content', {
            'fields': ('description',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )


@admin.register(LearningObjective)
class LearningObjectiveAdmin(admin.ModelAdmin):
    list_display = ['title', 'objective_type', 'get_modules', 'is_active', 'created_at']
    list_filter = ['objective_type', 'learning_modules', 'is_active']
    search_fields = ['title', 'description']
    filter_horizontal = ['learning_modules']
    ordering = ['objective_type', 'title']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'objective_type')
        }),
        ('Content', {
            'fields': ('description', 'success_criteria')
        }),
        ('Curriculum Alignment', {
            'fields': ('learning_modules',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )
    
    def get_modules(self, obj):
        return ", ".join([module.name for module in obj.learning_modules.all()[:3]])
    get_modules.short_description = 'Learning Modules'


# Game Content Admin

class ScenarioInline(admin.TabularInline):
    model = Scenario
    extra = 0
    fields = ['order', 'title', 'scenario_type', 'urgency_level', 'is_active']
    readonly_fields = ['created_at']


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['title', 'game_type', 'difficulty_level', 'player_range', 'duration', 'is_active']
    list_filter = ['game_type', 'difficulty_level', 'is_active', 'target_age_min']
    search_fields = ['title', 'subtitle', 'description']
    filter_horizontal = ['learning_objectives']
    inlines = [ScenarioInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subtitle', 'game_type', 'cover_image')
        }),
        ('Game Content', {
            'fields': ('description', 'context', 'introduction_text')
        }),
        ('Game Configuration', {
            'fields': (
                ('min_players', 'max_players'), 
                'estimated_duration',
                'difficulty_level',
                ('target_age_min', 'target_age_max')
            )
        }),
        ('Learning Objectives', {
            'fields': ('learning_objectives',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )
    
    def player_range(self, obj):
        return f"{obj.min_players}-{obj.max_players} players"
    player_range.short_description = 'Players'
    
    def duration(self, obj):
        return f"{obj.estimated_duration} min"
    duration.short_description = 'Duration'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'authority_level', 'color_preview', 'expertise_preview', 'is_active']
    list_filter = ['authority_level', 'is_active']
    search_fields = ['name', 'short_name', 'description']
    ordering = ['-authority_level', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'short_name', 'description')
        }),
        ('Role Characteristics', {
            'fields': ('authority_level', 'expertise_areas')
        }),
        ('Visual Representation', {
            'fields': ('icon', 'color')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )
    
    def color_preview(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; display: inline-block;"></div>',
            obj.color
        )
    color_preview.short_description = 'Color'
    
    def expertise_preview(self, obj):
        if obj.expertise_areas:
            return ", ".join(obj.expertise_areas[:3])
        return "None"
    expertise_preview.short_description = 'Expertise'


# Scenario and Action Admin

class ActionInline(admin.TabularInline):
    model = Action
    extra = 0
    fields = ['role', 'title', 'action_type', 'resource_cost', 'time_required', 'is_active']


class OutcomeInline(admin.TabularInline):
    model = Outcome
    extra = 0
    fields = ['title', 'outcome_type', 'success_score', 'is_active']


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ['title', 'game', 'scenario_type', 'urgency_level', 'location', 'get_roles', 'is_active']
    list_filter = ['scenario_type', 'urgency_level', 'game', 'is_active']
    search_fields = ['title', 'situation_description', 'location']
    filter_horizontal = ['required_roles', 'learning_objectives', 'prerequisite_scenarios']
    inlines = [ActionInline, OutcomeInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('game', 'title', 'scenario_type', 'order')
        }),
        ('Scenario Content', {
            'fields': ('situation_description', 'urgency_level')
        }),
        ('Context', {
            'fields': ('location', 'cultural_context')
        }),
        ('Game Mechanics', {
            'fields': ('time_limit', 'required_roles', 'prerequisite_scenarios')
        }),
        ('Learning', {
            'fields': ('learning_objectives',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )
    
    def get_roles(self, obj):
        return ", ".join([role.short_name for role in obj.required_roles.all()])
    get_roles.short_description = 'Required Roles'


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ['title', 'scenario', 'role', 'action_type', 'resource_cost', 'time_required', 'is_active']
    list_filter = ['action_type', 'resource_cost', 'time_required', 'scenario__game', 'role', 'is_active']
    search_fields = ['title', 'description']
    filter_horizontal = ['requires_other_roles']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('scenario', 'role', 'title', 'action_type')
        }),
        ('Action Details', {
            'fields': ('description', 'effectiveness_factors')
        }),
        ('Characteristics', {
            'fields': (('resource_cost', 'time_required'),)
        }),
        ('Dependencies', {
            'fields': ('requires_other_roles',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Outcome)
class OutcomeAdmin(admin.ModelAdmin):
    list_display = ['title', 'scenario', 'outcome_type', 'success_score', 'get_actions', 'is_active']
    list_filter = ['outcome_type', 'success_score', 'scenario__game', 'is_active']
    search_fields = ['title', 'description']
    filter_horizontal = ['required_actions']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('scenario', 'title', 'outcome_type', 'success_score')
        }),
        ('Outcome Content', {
            'fields': ('description', 'immediate_consequences', 'long_term_effects')
        }),
        ('Triggering Conditions', {
            'fields': ('required_actions', 'probability_weight')
        }),
        ('Learning Content', {
            'fields': ('learning_points', 'reflection_questions')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )
    
    def get_actions(self, obj):
        try:
            actions = []
            for action in obj.required_actions.all()[:2]:
                if action.role:
                    actions.append(f"{action.role.short_name}: {action.title}")
                else:
                    actions.append(action.title)
            return ", ".join(actions) if actions else "None"
        except Exception as e:
            return f"Error: {str(e)}"
    get_actions.short_description = 'Required Actions'


# Session Management Admin

class PlayerActionInline(admin.TabularInline):
    model = PlayerAction
    extra = 0
    readonly_fields = ['player_name', 'role', 'action', 'decision_time']
    fields = ['player_name', 'role', 'action', 'reasoning', 'decision_time']


class ReflectionResponseInline(admin.TabularInline):
    model = ReflectionResponse
    extra = 0
    readonly_fields = ['player_name', 'role_played', 'learning_objective', 'created_at']
    fields = ['player_name', 'role_played', 'learning_objective', 'confidence_level', 'engagement_level']


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['session_code', 'game', 'status', 'facilitator', 'current_scenario', 'created_at', 'player_count']
    list_filter = ['status', 'game', 'allow_spectators', 'auto_assign_roles']
    search_fields = ['session_code', 'game__title', 'facilitator__username']
    readonly_fields = ['session_code', 'created_at']
    inlines = [PlayerActionInline, ReflectionResponseInline]
    
    fieldsets = (
        ('Session Information', {
            'fields': ('game', 'session_code', 'facilitator', 'status')
        }),
        ('Current State', {
            'fields': ('current_scenario',)
        }),
        ('Timing', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
        ('Settings', {
            'fields': ('allow_spectators', 'auto_assign_roles')
        }),
        ('Session Data', {
            'fields': ('session_data',),
            'classes': ('collapse',)
        }),
    )
    
    def player_count(self, obj):
        return obj.player_actions.values('player_session_id').distinct().count()
    player_count.short_description = 'Players'


@admin.register(PlayerAction)
class PlayerActionAdmin(admin.ModelAdmin):
    list_display = ['player_name', 'role', 'action', 'session', 'scenario', 'decision_time']
    list_filter = ['session', 'scenario', 'role', 'decision_time']
    search_fields = ['player_name', 'action__title', 'reasoning']
    readonly_fields = ['decision_time']
    
    fieldsets = (
        ('Action Information', {
            'fields': ('session', 'scenario', 'role', 'action')
        }),
        ('Player Information', {
            'fields': ('player_name', 'player_session_id')
        }),
        ('Decision Details', {
            'fields': ('reasoning', 'round_number', 'is_final_decision', 'decision_time')
        }),
    )


@admin.register(ReflectionResponse)
class ReflectionResponseAdmin(admin.ModelAdmin):
    list_display = ['player_name', 'role_played', 'learning_objective', 'confidence_level', 'engagement_level', 'created_at']
    list_filter = ['session', 'learning_objective', 'role_played', 'confidence_level', 'engagement_level']
    search_fields = ['player_name', 'question', 'response']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Response Information', {
            'fields': ('session', 'scenario', 'learning_objective')
        }),
        ('Player Information', {
            'fields': ('player_name', 'player_session_id', 'role_played')
        }),
        ('Reflection Content', {
            'fields': ('question', 'response')
        }),
        ('Assessment', {
            'fields': ('confidence_level', 'engagement_level', 'created_at')
        }),
    )


# Custom Admin Site Configuration
admin.site.site_header = "DecipherWorld Group Learning Admin"
admin.site.site_title = "Group Learning Admin"
admin.site.index_title = "Welcome to Group Learning Administration"
