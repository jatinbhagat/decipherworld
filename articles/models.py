from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from tinymce.models import HTMLField


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    
    class Meta:
        verbose_name_plural = "categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    content = HTMLField()
    meta_description = models.CharField(
        max_length=160, 
        help_text="SEO meta description (max 160 characters)"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_on']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('articles:article_detail', kwargs={'slug': self.slug})
    
    def get_comments_count(self):
        """Return total number of comments for this article"""
        return self.comments.count()
    
    def get_likes_count(self):
        """Return total number of likes for this article"""
        return self.likes.count()
    
    def get_shares_count(self):
        """Return total number of shares for this article"""
        return self.shares.count()


class Comment(models.Model):
    """Comments on articles - requires user authentication"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=1000, help_text="Maximum 1000 characters")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['article', 'created_at']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f'Comment by {self.author.username} on {self.article.title}'
    
    def save(self, *args, **kwargs):
        if self.pk:  # If updating existing comment
            self.is_edited = True
        super().save(*args, **kwargs)


class ArticleLike(models.Model):
    """Likes for articles - supports both authenticated and anonymous users"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Ensure one like per user/session per article
        constraints = [
            models.UniqueConstraint(
                fields=['article', 'user'],
                condition=models.Q(user__isnull=False),
                name='unique_user_like'
            ),
            models.UniqueConstraint(
                fields=['article', 'session_key'],
                condition=models.Q(session_key__isnull=False),
                name='unique_session_like'
            )
        ]
        indexes = [
            models.Index(fields=['article']),
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
    
    def __str__(self):
        if self.user:
            return f'Like by {self.user.username} on {self.article.title}'
        return f'Anonymous like on {self.article.title}'


class ArticleShare(models.Model):
    """Track social media shares for analytics"""
    
    PLATFORM_CHOICES = [
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('email', 'Email'),
        ('copy_link', 'Copy Link'),
    ]
    
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='shares')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['article', 'platform']),
            models.Index(fields=['shared_at']),
        ]
    
    def __str__(self):
        return f'{self.article.title} shared on {self.get_platform_display()}'
