from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import json
import re
from .models import Article, Comment, ArticleLike, ArticleShare


class ArticleListView(ListView):
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 10


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object
        
        # Add engagement data to context
        context['comments'] = article.comments.select_related('author').order_by('created_at')
        context['comments_count'] = article.get_comments_count()
        context['likes_count'] = article.get_likes_count()
        context['shares_count'] = article.get_shares_count()
        
        # Check if current user/session has liked this article
        if self.request.user.is_authenticated:
            context['user_has_liked'] = ArticleLike.objects.filter(
                article=article, user=self.request.user
            ).exists()
        else:
            session_key = self.request.session.session_key
            if session_key:
                context['user_has_liked'] = ArticleLike.objects.filter(
                    article=article, session_key=session_key
                ).exists()
            else:
                context['user_has_liked'] = False
        
        return context


# COMMENT MANAGEMENT VIEWS

@login_required
@require_http_methods(["POST"])
def add_comment(request, slug):
    """Add a comment to an article (AJAX)"""
    article = get_object_or_404(Article, slug=slug)
    
    try:
        # Rate limiting check (3 comments per minute)
        recent_comments = Comment.objects.filter(
            author=request.user,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=1)
        ).count()
        
        if recent_comments >= 3:
            return JsonResponse({
                'success': False,
                'error': 'Rate limit exceeded. Please wait before commenting again.'
            }, status=429)
        
        # Get and validate content
        content = request.POST.get('content', '').strip()
        if not content or len(content) > 1000:
            return JsonResponse({
                'success': False,
                'error': 'Comment must be between 1 and 1000 characters.'
            }, status=400)
        
        # Basic spam protection (honeypot field)
        honeypot = request.POST.get('email', '')  # Should be empty
        if honeypot:
            return JsonResponse({
                'success': False,
                'error': 'Spam detected.'
            }, status=400)
        
        # Content validation (no harmful patterns)
        if re.search(r'<script|javascript:|data:', content, re.IGNORECASE):
            return JsonResponse({
                'success': False,
                'error': 'Invalid content detected.'
            }, status=400)
        
        # Create comment
        comment = Comment.objects.create(
            article=article,
            author=request.user,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': comment.author.get_full_name() or comment.author.username,
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'is_edited': comment.is_edited,
                'can_edit': True  # User just created it
            },
            'comments_count': article.get_comments_count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Failed to add comment. Please try again.'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def edit_comment(request, comment_id):
    """Edit a comment (AJAX)"""
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    
    try:
        content = request.POST.get('content', '').strip()
        if not content or len(content) > 1000:
            return JsonResponse({
                'success': False,
                'error': 'Comment must be between 1 and 1000 characters.'
            }, status=400)
        
        # Content validation
        if re.search(r'<script|javascript:|data:', content, re.IGNORECASE):
            return JsonResponse({
                'success': False,
                'error': 'Invalid content detected.'
            }, status=400)
        
        comment.content = content
        comment.save()  # This will set is_edited = True
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'is_edited': comment.is_edited,
                'updated_at': comment.updated_at.strftime('%B %d, %Y at %I:%M %p')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Failed to edit comment. Please try again.'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_comment(request, comment_id):
    """Delete a comment (AJAX)"""
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    article = comment.article
    
    try:
        comment.delete()
        return JsonResponse({
            'success': True,
            'comments_count': article.get_comments_count()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Failed to delete comment. Please try again.'
        }, status=500)


# LIKE SYSTEM VIEWS

@require_http_methods(["POST"])
def toggle_like(request, slug):
    """Toggle like/unlike for an article (AJAX) - supports anonymous users"""
    article = get_object_or_404(Article, slug=slug)
    
    try:
        # Get user IP for rate limiting
        ip_address = get_client_ip(request)
        
        # Rate limiting check (10 likes per hour per IP)
        recent_likes = ArticleLike.objects.filter(
            ip_address=ip_address,
            created_at__gte=timezone.now() - timezone.timedelta(hours=1)
        ).count()
        
        if recent_likes >= 10:
            return JsonResponse({
                'success': False,
                'error': 'Rate limit exceeded. Please wait before liking again.'
            }, status=429)
        
        if request.user.is_authenticated:
            # Authenticated user
            like, created = ArticleLike.objects.get_or_create(
                article=article,
                user=request.user,
                defaults={'ip_address': ip_address}
            )
            if not created:
                like.delete()
                liked = False
            else:
                liked = True
        else:
            # Anonymous user - use session
            if not request.session.session_key:
                request.session.create()
            
            session_key = request.session.session_key
            like, created = ArticleLike.objects.get_or_create(
                article=article,
                session_key=session_key,
                defaults={'ip_address': ip_address}
            )
            if not created:
                like.delete()
                liked = False
            else:
                liked = True
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': article.get_likes_count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Failed to process like. Please try again.'
        }, status=500)


# SHARE TRACKING VIEWS

@require_http_methods(["POST"])
def track_share(request, slug):
    """Track social media shares (AJAX)"""
    article = get_object_or_404(Article, slug=slug)
    
    try:
        platform = request.POST.get('platform', '')
        if platform not in dict(ArticleShare.PLATFORM_CHOICES):
            return JsonResponse({
                'success': False,
                'error': 'Invalid platform.'
            }, status=400)
        
        # Create share record
        ArticleShare.objects.create(
            article=article,
            platform=platform,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
        )
        
        return JsonResponse({
            'success': True,
            'shares_count': article.get_shares_count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Failed to track share.'
        }, status=500)


# UTILITY FUNCTIONS

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
