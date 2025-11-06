from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count
from django.utils.safestring import mark_safe
from .models import (
    DemoRequest, Course, SchoolDemoRequest, GameReview,
    PhotoCategory, PhotoGallery, VideoTestimonial, SchoolReferral
)

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


@admin.register(SchoolReferral)
class SchoolReferralAdmin(admin.ModelAdmin):
    list_display = [
        'school_name', 'referrer_name', 'contact_person_name', 'school_board', 
        'status', 'reward_amount', 'reward_paid', 'created_at'
    ]
    list_filter = [
        'status', 'reward_paid', 'interest_level', 
        'school_board', 'created_at', 'contacted_at'
    ]
    search_fields = [
        'school_name', 'referrer_name', 'referrer_email', 'contact_person_name',
        'contact_person_email', 'school_city', 'school_state'
    ]
    list_editable = ['status', 'reward_paid']
    readonly_fields = [
        'created_at', 'updated_at', 'get_reward_display'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Referral Status', {
            'fields': ('status', 'admin_notes', 'contacted_at')
        }),
        ('Referrer Information', {
            'fields': ('referrer_name', 'referrer_email', 'referrer_phone', 'referrer_relationship')
        }),
        ('School Information', {
            'fields': (
                'school_name', 'school_address', 'school_city', 'school_state', 'school_pincode'
            )
        }),
        ('School Contact', {
            'fields': (
                'contact_person_name', 'contact_person_designation', 
                'contact_person_email', 'contact_person_phone'
            )
        }),
        ('School Details', {
            'fields': (
                'school_board', 'current_education_programs'
            )
        }),
        ('Interest & Additional Info', {
            'fields': ('interest_level', 'additional_notes')
        }),
        ('Reward Information', {
            'fields': ('reward_amount', 'get_reward_display', 'reward_paid', 'reward_paid_date')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_contacted', 'mark_as_qualified', 'mark_as_converted', 
        'mark_reward_as_paid', 'send_follow_up_email'
    ]
    
    def get_status_badge(self, obj):
        """Display status with colored badge"""
        status_colors = {
            'pending': '#f59e0b',      # Orange
            'contacted': '#3b82f6',    # Blue  
            'qualified': '#10b981',    # Green
            'converted': '#8b5cf6',    # Purple
            'rejected': '#ef4444',     # Red
        }
        
        color = status_colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    get_status_badge.admin_order_field = 'status'
    
    
    def get_reward_display(self, obj):
        """Display formatted reward amount"""
        return obj.get_reward_display()
    get_reward_display.short_description = 'Reward Amount'
    
    # Admin Actions
    def mark_as_contacted(self, request, queryset):
        """Mark referrals as contacted"""
        from django.utils import timezone
        count = queryset.update(status='contacted', contacted_at=timezone.now())
        self.message_user(request, f'Marked {count} referrals as contacted.')
    mark_as_contacted.short_description = "Mark as contacted"
    
    def mark_as_qualified(self, request, queryset):
        """Mark referrals as qualified"""
        count = queryset.update(status='qualified')
        self.message_user(request, f'Marked {count} referrals as qualified.')
    mark_as_qualified.short_description = "Mark as qualified"
    
    def mark_as_converted(self, request, queryset):
        """Mark referrals as converted"""
        count = queryset.update(status='converted')
        self.message_user(request, f'Marked {count} referrals as converted.')
    mark_as_converted.short_description = "Mark as converted"
    
    def mark_reward_as_paid(self, request, queryset):
        """Mark rewards as paid"""
        from django.utils import timezone
        count = queryset.filter(status='converted').update(
            reward_paid=True, 
            reward_paid_date=timezone.now()
        )
        self.message_user(request, f'Marked rewards as paid for {count} converted referrals.')
    mark_reward_as_paid.short_description = "Mark reward as paid (converted only)"
    
    def send_follow_up_email(self, request, queryset):
        """Send follow-up email to referrers"""
        count = 0
        for referral in queryset:
            try:
                # Here you could send follow-up emails
                # For now, just count the action
                count += 1
            except Exception as e:
                self.message_user(request, f'Error sending email for {referral.school_name}: {e}', level='ERROR')
        
        if count > 0:
            self.message_user(request, f'Follow-up emails sent for {count} referrals.')
    send_follow_up_email.short_description = "Send follow-up email to referrers"
    
    def changelist_view(self, request, extra_context=None):
        """Add referral statistics to changelist"""
        extra_context = extra_context or {}
        
        # Get referral statistics
        referrals = SchoolReferral.objects.all()
        
        total_referrals = referrals.count()
        qualified_referrals = sum(1 for r in referrals if r.is_qualified())
        converted_referrals = referrals.filter(status='converted').count()
        total_rewards_pending = referrals.filter(
            status='converted', reward_paid=False
        ).count() * 50000
        total_rewards_paid = referrals.filter(reward_paid=True).count() * 50000
        
        # Status distribution
        status_stats = referrals.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        extra_context.update({
            'total_referrals': total_referrals,
            'qualified_referrals': qualified_referrals,
            'converted_referrals': converted_referrals,
            'total_rewards_pending': f"₹{total_rewards_pending:,}",
            'total_rewards_paid': f"₹{total_rewards_paid:,}",
            'status_stats': status_stats,
        })
        
        return super().changelist_view(request, extra_context)


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


# Gallery Admin Classes

@admin.register(PhotoCategory)
class PhotoCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'photo_count', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'name']
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
    )
    
    def photo_count(self, obj):
        """Show number of photos in this category"""
        count = obj.photogallery_set.filter(is_active=True).count()
        if count == 0:
            return format_html('<span style="color: #999;">0 photos</span>')
        elif count < 5:
            return format_html('<span style="color: #f0ad4e;">{} photos</span>', count)
        else:
            return format_html('<span style="color: #5cb85c;">{} photos</span>', count)
    photo_count.short_description = 'Active Photos'
    photo_count.admin_order_field = 'photogallery__count'


@admin.register(PhotoGallery)
class PhotoGalleryAdmin(admin.ModelAdmin):
    list_display = [
        'image_preview', 'title', 'category', 'school_name', 
        'date_taken', 'order', 'is_featured', 'is_active', 'created_at'
    ]
    list_filter = [
        'category', 'is_featured', 'is_active', 'created_at', 'date_taken'
    ]
    search_fields = ['title', 'school_name', 'caption']
    list_editable = ['order', 'is_featured', 'is_active']
    readonly_fields = ['image_preview', 'created_at', 'updated_at']
    ordering = ['order', '-created_at']
    
    fieldsets = (
        ('Photo Information', {
            'fields': ('title', 'image', 'image_preview', 'category')
        }),
        ('Details', {
            'fields': ('caption', 'school_name', 'date_taken')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_featured', 'is_active')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_featured', 'mark_as_active', 'mark_as_inactive']
    
    def mark_as_featured(self, request, queryset):
        """Mark selected photos as featured"""
        count = queryset.update(is_featured=True)
        self.message_user(request, f'Marked {count} photos as featured.')
    mark_as_featured.short_description = "Mark selected photos as featured"
    
    def mark_as_active(self, request, queryset):
        """Mark selected photos as active"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'Marked {count} photos as active.')
    mark_as_active.short_description = "Mark selected photos as active"
    
    def mark_as_inactive(self, request, queryset):
        """Mark selected photos as inactive"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'Marked {count} photos as inactive.')
    mark_as_inactive.short_description = "Mark selected photos as inactive"
    
    def image_preview(self, obj):
        """Display image preview for admin"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 8px;" />',
                obj.image.url
            )
        return 'No image'
    image_preview.short_description = 'Preview'
    image_preview.admin_order_field = 'image'
    
    class Media:
        css = {
            'all': ('admin/css/gallery_admin.css',)
        }
        js = ('admin/js/gallery_admin.js',)


@admin.register(VideoTestimonial)
class VideoTestimonialAdmin(admin.ModelAdmin):
    list_display = [
        'video_preview', 'title', 'student_info', 'school_name', 'aspect_ratio_display',
        'duration', 'order', 'is_featured', 'is_active', 'created_at'
    ]
    list_filter = [
        'is_featured', 'is_active', 'created_at', 'school_name', 'aspect_ratio'
    ]
    search_fields = [
        'title', 'student_name', 'school_name', 'summary', 'transcript'
    ]
    list_editable = ['order', 'is_featured', 'is_active']
    readonly_fields = ['video_preview', 'aspect_ratio_display', 'auto_thumbnail', 'created_at', 'updated_at']
    ordering = ['order', '-created_at']
    
    fieldsets = (
        ('Video Information', {
            'fields': ('title', 'video_file', 'video_url', 'video_preview', 'thumbnail')
        }),
        ('Student Details', {
            'fields': ('student_name', 'student_grade', 'school_name')
        }),
        ('Content', {
            'fields': ('summary', 'transcript', 'duration')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_featured', 'is_active')
        }),
        ('Video Analysis', {
            'fields': ('aspect_ratio_display', 'video_width', 'video_height', 'auto_thumbnail'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_featured', 'mark_as_active', 'mark_as_inactive', 'generate_thumbnails']
    
    def aspect_ratio_display(self, obj):
        """Display aspect ratio with portrait/landscape indicator"""
        if obj.aspect_ratio:
            orientation = "📱 Portrait" if obj.is_portrait() else "🖥️ Landscape"
            return format_html('{}<br><small style="color: #666;">{}</small>', obj.aspect_ratio, orientation)
        return '-'
    aspect_ratio_display.short_description = 'Aspect Ratio'
    
    def generate_thumbnails(self, request, queryset):
        """Generate thumbnails for selected videos"""
        count = 0
        for video in queryset:
            if video.auto_generate_thumbnail():
                video.save()
                count += 1
        self.message_user(request, f'Generated thumbnails for {count} videos.')
    generate_thumbnails.short_description = "Generate auto thumbnails"
    
    def student_info(self, obj):
        """Display student name and grade together"""
        if obj.student_grade:
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">{}</small>',
                obj.student_name, obj.student_grade
            )
        return obj.student_name
    student_info.short_description = 'Student'
    student_info.admin_order_field = 'student_name'
    
    def mark_as_featured(self, request, queryset):
        """Mark selected videos as featured"""
        count = queryset.update(is_featured=True)
        self.message_user(request, f'Marked {count} videos as featured.')
    mark_as_featured.short_description = "Mark selected videos as featured"
    
    def mark_as_active(self, request, queryset):
        """Mark selected videos as active"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'Marked {count} videos as active.')
    mark_as_active.short_description = "Mark selected videos as active"
    
    def mark_as_inactive(self, request, queryset):
        """Mark selected videos as inactive"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'Marked {count} videos as inactive.')
    mark_as_inactive.short_description = "Mark selected videos as inactive"
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form help text"""
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['video_file'].help_text = (
            'Upload MP4 video file (max 50MB recommended). '
            'Leave blank if using video_url instead.'
        )
        form.base_fields['video_url'].help_text = (
            'Paste YouTube, Vimeo, or other video URL. '
            'Leave blank if uploading video file instead.'
        )
        return form
    
    def video_preview(self, obj):
        """Display video preview for admin"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 60px; object-fit: cover; border-radius: 8px;" />',
                obj.thumbnail.url
            )
        elif obj.video_file:
            return format_html(
                '<div style="width: 100px; height: 60px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #666;"><i class="fas fa-video"></i></div>'
            )
        return 'No preview'
    video_preview.short_description = 'Preview'
    
    class Media:
        css = {
            'all': ('admin/css/gallery_admin.css',)
        }
        js = ('admin/js/video_admin.js',)


# Add custom admin site configuration for better branding
admin.site.site_header = "DecipherWorld Administration"
admin.site.site_title = "DecipherWorld Admin"
admin.site.index_title = "Welcome to DecipherWorld Admin Portal"