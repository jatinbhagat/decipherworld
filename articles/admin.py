from django.contrib import admin
from .models import Article, Category, Comment, ArticleLike, ArticleShare


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'created_on']
    list_filter = ['category', 'author', 'created_on']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_on', 'last_modified']
    
    fieldsets = (
        ('Article Content', {
            'fields': ('title', 'slug', 'author', 'category', 'content')
        }),
        ('SEO', {
            'fields': ('meta_description',)
        }),
        ('Timestamps', {
            'fields': ('created_on', 'last_modified'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queries for admin interface"""
        qs = super().get_queryset(request)
        return qs.select_related('author', 'category').prefetch_related('comments', 'likes', 'shares')
    
    def comments_count(self, obj):
        """Display comment count in admin list"""
        return obj.get_comments_count()
    comments_count.short_description = "Comments"
    
    def likes_count(self, obj):
        """Display likes count in admin list"""
        return obj.get_likes_count()
    likes_count.short_description = "Likes"
    
    def shares_count(self, obj):
        """Display shares count in admin list"""
        return obj.get_shares_count()
    shares_count.short_description = "Shares"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['content_preview', 'author', 'article', 'created_at', 'is_edited']
    list_filter = ['created_at', 'is_edited', 'article__category']
    search_fields = ['content', 'author__username', 'article__title']
    readonly_fields = ['created_at', 'updated_at', 'is_edited']
    list_select_related = ['author', 'article']
    list_per_page = 25
    
    fieldsets = (
        ('Comment Details', {
            'fields': ('article', 'author', 'content')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_edited'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Show preview of comment content"""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = "Content"
    
    def get_queryset(self, request):
        """Optimize queries for admin interface"""
        qs = super().get_queryset(request)
        return qs.select_related('author', 'article')


@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    list_display = ['article', 'user_or_anonymous', 'ip_address', 'created_at']
    list_filter = ['created_at', 'article__category']
    search_fields = ['article__title', 'user__username', 'ip_address']
    readonly_fields = ['created_at', 'ip_address']
    list_select_related = ['article', 'user']
    list_per_page = 50
    
    fieldsets = (
        ('Like Details', {
            'fields': ('article', 'user', 'session_key')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_or_anonymous(self, obj):
        """Show user or anonymous label"""
        return obj.user.username if obj.user else 'Anonymous'
    user_or_anonymous.short_description = "User"
    
    def get_queryset(self, request):
        """Optimize queries for admin interface"""
        qs = super().get_queryset(request)
        return qs.select_related('article', 'user')


@admin.register(ArticleShare)
class ArticleShareAdmin(admin.ModelAdmin):
    list_display = ['article', 'platform', 'ip_address', 'shared_at']
    list_filter = ['platform', 'shared_at', 'article__category']
    search_fields = ['article__title', 'ip_address']
    readonly_fields = ['shared_at', 'ip_address', 'user_agent']
    list_select_related = ['article']
    list_per_page = 50
    
    fieldsets = (
        ('Share Details', {
            'fields': ('article', 'platform')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'shared_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queries for admin interface"""
        qs = super().get_queryset(request)
        return qs.select_related('article')
