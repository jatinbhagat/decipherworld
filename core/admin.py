from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count
from django.utils.safestring import mark_safe
from .models import DemoRequest, Course, SchoolDemoRequest, GameReview

@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'email', 'get_full_mobile_number', 'created_at']
    list_filter = ['created_at', 'country_code']
    search_fields = ['name', 'school', 'email', 'mobile_number']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email')
        }),
        ('Institution', {
            'fields': ('school',)
        }),
        ('Contact Information', {
            'fields': ('country_code', 'mobile_number')
        }),
        ('Request Details', {
            'fields': ('message',)
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_mobile_number(self, obj):
        """Display formatted mobile number with country code and flag"""
        if obj.mobile_number and obj.mobile_number != "0000000000":
            # Extract flag from country code choices
            country_display = dict(obj._meta.get_field('country_code').choices).get(obj.country_code, obj.country_code)
            flag = country_display.split(' ')[0] if ' ' in country_display else '📱'
            return format_html('{} {}', flag, obj.get_full_mobile_number())
        return 'Not provided'
    get_full_mobile_number.short_description = 'Mobile Number'
    get_full_mobile_number.admin_order_field = 'mobile_number'

@admin.register(SchoolDemoRequest)
class SchoolDemoRequestAdmin(admin.ModelAdmin):
    list_display = ['school_name', 'contact_person', 'email', 'get_full_mobile_number', 'city', 'student_count', 'get_products_display', 'is_contacted', 'created_at']
    list_filter = ['is_contacted', 'created_at', 'city', 'country_code']
    search_fields = ['school_name', 'contact_person', 'email', 'city', 'mobile_number']
    readonly_fields = ['created_at']
    filter_horizontal = []
    
    fieldsets = (
        ('School Information', {
            'fields': ('school_name', 'contact_person', 'email', 'city', 'student_count')
        }),
        ('Contact Information', {
            'fields': ('country_code', 'mobile_number')
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
    
    def get_full_mobile_number(self, obj):
        """Display formatted mobile number with country code and flag"""
        if obj.mobile_number and obj.mobile_number != "0000000000":
            # Extract flag from country code choices
            country_display = dict(obj._meta.get_field('country_code').choices).get(obj.country_code, obj.country_code)
            flag = country_display.split(' ')[0] if ' ' in country_display else '📱'
            return format_html('{} {}', flag, obj.get_full_mobile_number())
        return 'Not provided'
    get_full_mobile_number.short_description = 'Mobile Number'
    get_full_mobile_number.admin_order_field = 'mobile_number'
    
    def get_products_display(self, obj):
        """Display interested products in a readable format"""
        return ', '.join(obj.get_products_display())
    get_products_display.short_description = 'Interested Products'

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description']


@admin.register(GameReview)
class GameReviewAdmin(admin.ModelAdmin):
    list_display = [
        'game_display', 'rating_stars', 'player_name', 'session_preview', 
        'player_age', 'created_at', 'ip_preview'
    ]
    list_filter = [
        'game_type', 'rating', 'created_at', 'player_age'
    ]
    search_fields = [
        'player_name', 'session_id', 'review_text', 'game_type'
    ]
    readonly_fields = [
        'created_at', 'ip_address', 'game_display', 'rating_stars', 
        'session_preview', 'review_preview'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Game Information', {
            'fields': ('game_type', 'game_display', 'session_id', 'session_preview')
        }),
        ('Player Information', {
            'fields': ('player_name', 'player_age')
        }),
        ('Review Content', {
            'fields': ('rating', 'rating_stars', 'review_text', 'review_preview')
        }),
        ('System Information', {
            'fields': ('created_at', 'ip_address'),
            'classes': ('collapse',)
        }),
    )
    
    def game_display(self, obj):
        """Display human-readable game name with icon"""
        game_icons = {
            'password_fortress': '🔐',
            'cyberbully_crisis': '🛡️', 
            'robotic_buddy': '🤖',
            'animal_classification': '🦁',
            'emotion_recognition': '😊',
            'group_learning': '👥',
            'constitution_basic': '📜',
            'constitution_advanced': '🏛️',
            'financial_literacy': '💰',
            'entrepreneurship': '🚀'
        }
        icon = game_icons.get(obj.game_type, '🎮')
        name = obj.get_game_display()
        return format_html(f'{icon} {name}')
    game_display.short_description = 'Game'
    game_display.admin_order_field = 'game_type'
    
    def rating_stars(self, obj):
        """Display rating as colored stars"""
        stars = '⭐' * obj.rating
        empty_stars = '☆' * (5 - obj.rating)
        color = ['#ff4444', '#ff8800', '#ffaa00', '#88dd00', '#00dd44'][obj.rating - 1]
        return format_html(
            '<span style="color: {}; font-size: 16px;">{}</span><span style="color: #ccc;">{}</span>',
            color, stars, empty_stars
        )
    rating_stars.short_description = 'Rating'
    rating_stars.admin_order_field = 'rating'
    
    def session_preview(self, obj):
        """Display session ID preview"""
        if obj.session_id:
            return obj.session_id[:12] + '...' if len(obj.session_id) > 12 else obj.session_id
        return '-'
    session_preview.short_description = 'Session'
    
    def ip_preview(self, obj):
        """Display IP address preview"""
        if obj.ip_address:
            return str(obj.ip_address)
        return '-'
    ip_preview.short_description = 'IP Address'
    
    def review_preview(self, obj):
        """Display review text preview for detail view"""
        if obj.review_text:
            preview = obj.review_text[:100] + '...' if len(obj.review_text) > 100 else obj.review_text
            return format_html('<div style="max-width: 400px; white-space: pre-wrap;">{}</div>', preview)
        return 'No review text provided'
    review_preview.short_description = 'Review Preview'
    
    def get_queryset(self, request):
        """Optimize queries with select_related if needed"""
        return super().get_queryset(request)
    
    def changelist_view(self, request, extra_context=None):
        """Add analytics to the changelist view"""
        extra_context = extra_context or {}
        
        # Calculate review statistics
        reviews = GameReview.objects.all()
        
        # Overall statistics
        total_reviews = reviews.count()
        avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        
        # Game type statistics
        game_stats = reviews.values('game_type').annotate(
            count=Count('id'),
            avg_rating=Avg('rating')
        ).order_by('-count')
        
        # Rating distribution
        rating_distribution = reviews.values('rating').annotate(
            count=Count('id')
        ).order_by('rating')
        
        # Recent activity (last 7 days)
        from django.utils import timezone
        from datetime import timedelta
        recent_date = timezone.now() - timedelta(days=7)
        recent_reviews = reviews.filter(created_at__gte=recent_date).count()
        
        extra_context.update({
            'total_reviews': total_reviews,
            'avg_rating': round(avg_rating, 1),
            'game_stats': game_stats,
            'rating_distribution': rating_distribution,
            'recent_reviews': recent_reviews,
        })
        
        return super().changelist_view(request, extra_context)
    
    class Media:
        css = {
            'all': ('admin/css/custom_game_review.css',)
        }


# Add custom admin site configuration for better branding
admin.site.site_header = "DecipherWorld Administration"
admin.site.site_title = "DecipherWorld Admin"
admin.site.index_title = "Welcome to DecipherWorld Admin Portal"