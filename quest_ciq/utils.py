"""
Utility functions and decorators for quest_ciq app.
"""
from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse

SESSION_KEY = "ciq_session_id"


def require_ciq_session(view_func):
    """
    Decorator to require a CIQ session for accessing student views.
    Redirects to join page if no session exists.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get(SESSION_KEY):
            # Redirect to join page with the slug from kwargs if available
            slug = kwargs.get('slug', 'classroom-innovation-quest')
            return redirect(reverse('quest_ciq:quest_join', kwargs={'slug': slug}))
        return view_func(request, *args, **kwargs)
    return _wrapped
