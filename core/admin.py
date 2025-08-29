from django.contrib import admin
from .models import DemoRequest, Course

@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'school', 'email']
    readonly_fields = ['created_at']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description']