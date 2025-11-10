"""
Feature flag management for Quest CIQ app
"""
from django.conf import settings
from django.http import Http404
from functools import wraps


def get_enable_ciq():
    """
    Get the ENABLE_CIQ feature flag value from settings.
    Returns False by default if not set.
    """
    return getattr(settings, 'ENABLE_CIQ', False)


def require_ciq_enabled(view_func):
    """
    Decorator to ensure CIQ feature is enabled.
    Returns 404 if the feature is disabled.

    Usage:
        @require_ciq_enabled
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not get_enable_ciq():
            raise Http404("Quest CIQ feature is not enabled")
        return view_func(request, *args, **kwargs)
    return wrapper


class CIQFeatureMixin:
    """
    Mixin for class-based views to check CIQ feature flag.
    Raises Http404 if feature is disabled.

    Usage:
        class MyView(CIQFeatureMixin, View):
            ...
    """
    def dispatch(self, request, *args, **kwargs):
        if not get_enable_ciq():
            raise Http404("Quest CIQ feature is not enabled")
        return super().dispatch(request, *args, **kwargs)
