from django.contrib.sitemaps import Sitemap
from django.urls import reverse

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