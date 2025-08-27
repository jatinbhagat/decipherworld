from django.contrib import admin
from .models import School, UserProfile, DemoRequest, Course

@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'school_name', 'role', 'status', 'created_at']
    list_filter = ['status', 'role', 'interests', 'created_at']
    search_fields = ['full_name', 'school_name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name', 'email', 'phone', 'school_name', 'role')
        }),
        ('Demo Details', {
            'fields': ('student_count_range', 'interests', 'preferred_demo_date', 'message')
        }),
        ('Status', {
            'fields': ('status', 'assigned_to', 'demo_scheduled_at', 'notes')
        }),
        ('Metadata', {
            'fields': ('source', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'difficulty_level', 'duration_weeks', 'is_active']
    list_filter = ['category', 'difficulty_level', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}