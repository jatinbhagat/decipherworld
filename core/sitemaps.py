from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.9
    changefreq = 'weekly'

    def items(self):
        return ['core:home', 'core:about', 'core:courses', 'core:teachers', 'core:schools', 
                'core:school-presentation', 'core:gallery', 'core:contact']

    def location(self, item):
        return reverse(item)

    def lastmod(self, obj):
        return None

class GamesHubSitemap(Sitemap):
    """Sitemap for Games Hub and Category Pages"""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'games:hub',
            'games:ai_learning',
            'games:cyber_security', 
            'games:financial_literacy',
            'games:constitution_basic',
            'games:constitution_advanced',
            'games:entrepreneurship',
            'games:group_learning',
            'games:stem_challenges',
            'games:language_adventures'
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, obj):
        return None

class AILearningGamesSitemap(Sitemap):
    """Sitemap for AI Learning Games (Robotic Buddy)"""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'games:robotic_buddy_landing',
            'games:simple_game_landing', 
            'games:drag_drop_game_landing',
            'robotic_buddy:home',
            'robotic_buddy:activities',
            'robotic_buddy:create_buddy',
            'robotic_buddy:my_buddy',
            'robotic_buddy:classification_game',
            'robotic_buddy:simple_game',
            'robotic_buddy:drag_drop_game',
            'robotic_buddy:emotion_game',
            'robotic_buddy:testing_phase',
            'robotic_buddy:learning_explanation',
            'robotic_buddy:buddy_stats',
            'robotic_buddy:achievements'
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, obj):
        return None

class CyberSecurityGamesSitemap(Sitemap):
    """Sitemap for Cyber Security Games (Cyber City)"""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'cyber_city:mission_hub',
            'cyber_city:quick_game'
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, obj):
        return None

class GroupLearningGamesSitemap(Sitemap):
    """Sitemap for Group Learning Games (excluding Climate Crisis)"""
    priority = 0.7
    changefreq = 'weekly'

    def items(self):
        return [
            'games:monsoon_mayhem_landing',
            'group_learning:game_list',
            'group_learning:constitution_quick_start'
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, obj):
        return None