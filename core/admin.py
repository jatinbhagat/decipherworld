from django.contrib import admin
from .models import DemoRequest, Course, SchoolDemoRequest

@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'school', 'email']
    readonly_fields = ['created_at']

@admin.register(SchoolDemoRequest)
class SchoolDemoRequestAdmin(admin.ModelAdmin):
    list_display = ['school_name', 'contact_person', 'email', 'city', 'student_count', 'is_contacted', 'created_at']
    list_filter = ['is_contacted', 'created_at', 'city']
    search_fields = ['school_name', 'contact_person', 'email', 'city']
    readonly_fields = ['created_at']
    filter_horizontal = []
    
    fieldsets = (
        ('School Information', {
            'fields': ('school_name', 'contact_person', 'email', 'phone', 'city', 'student_count')
        }),
        ('Product Interest', {
            'fields': ('interested_products',)
        }),
        ('Additional Details', {
            'fields': ('additional_requirements', 'preferred_demo_time')
        }),
        ('Admin', {
            'fields': ('is_contacted', 'created_at')
        }),
    )
    
    def get_products_display(self, obj):
        """Display interested products in a readable format"""
        return ', '.join(obj.get_products_display())
    get_products_display.short_description = 'Interested Products'
    
    list_display = ['school_name', 'contact_person', 'email', 'city', 'student_count', 'get_products_display', 'is_contacted', 'created_at']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description']