from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Course

class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.9
    changefreq = 'weekly'

    def items(self):
        return ['core:home', 'core:courses', 'core:teachers', 'core:schools', 
                'core:gallery', 'core:contact', 'core:school-presentation']

    def location(self, item):
        return reverse(item)

    def lastmod(self, obj):
        return None

class CourseSitemap(Sitemap):
    """Sitemap for course pages"""
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Course.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.created_at if hasattr(obj, 'created_at') else None

    def location(self, obj):
        # If you have individual course detail pages, modify this
        return '/courses/'