from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.9
    changefreq = 'weekly'

    def items(self):
        return ['core:home', 'core:about', 'core:courses', 'core:teachers', 'core:schools', 
                'core:gallery', 'core:contact']

    def location(self, item):
        return reverse(item)

    def lastmod(self, obj):
        return None

class GamesSitemap(Sitemap):
    """Sitemap for AI Learning Games"""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['robotic_buddy:home', 'robotic_buddy:activities', 'robotic_buddy:simple_game', 
                'robotic_buddy:drag_drop_game']

    def location(self, item):
        return reverse(item)

    def lastmod(self, obj):
        return None