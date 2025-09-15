
from django.contrib import admin
from .models import CyberCitySession, CyberCityPlayer, SecurityChallenge, PlayerChallenge, CyberBadge

@admin.register(CyberCitySession)
class CyberCitySessionAdmin(admin.ModelAdmin):
    list_display = ['session_code', 'status', 'mission_stage', 'city_security_level', 'created_at']
    list_filter = ['status', 'mission_stage', 'created_at']
    search_fields = ['session_code']
    readonly_fields = ['session_code', 'created_at', 'updated_at']

@admin.register(CyberCityPlayer)
class CyberCityPlayerAdmin(admin.ModelAdmin):
    list_display = ['hero_nickname', 'session', 'suit_style', 'total_score', 'challenges_completed', 'is_active']
    list_filter = ['suit_style', 'is_active', 'joined_at']
    search_fields = ['hero_nickname', 'player_name', 'session__session_code']
    readonly_fields = ['joined_at', 'last_activity']

@admin.register(SecurityChallenge)
class SecurityChallengeAdmin(admin.ModelAdmin):
    list_display = ['challenge_number', 'title', 'correct_answer']
    list_filter = ['challenge_number', 'correct_answer']
    search_fields = ['title', 'question_text']
    ordering = ['challenge_number']

@admin.register(PlayerChallenge)
class PlayerChallengeAdmin(admin.ModelAdmin):
    list_display = ['player', 'challenge', 'answer_given', 'is_correct', 'points_earned', 'answered_at']
    list_filter = ['is_correct', 'answered_at', 'challenge__challenge_number']
    search_fields = ['player__hero_nickname', 'challenge__title']

@admin.register(CyberBadge)
class CyberBadgeAdmin(admin.ModelAdmin):
    list_display = ['badge_id', 'name', 'icon', 'unlock_condition']
    search_fields = ['name', 'description']
