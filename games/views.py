from django.shortcuts import render
from django.views.generic import TemplateView
from group_learning.models import Game
from robotic_buddy.models import RoboticBuddy, GameActivity


class GamesHubView(TemplateView):
    """Main Games Hub - Overview of all game categories"""
    template_name = 'games/hub.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Educational Games Hub - AI Learning & Group Collaboration',
            'page_description': 'Discover interactive educational games including AI learning with robotic buddies and collaborative group scenarios. Transform learning into adventure with DecipherWorld\'s game-based education platform.',
            'group_learning_count': Game.objects.filter(is_active=True).count(),
            'robotic_buddy_count': RoboticBuddy.objects.count(),
            'ai_activities_count': GameActivity.objects.filter(is_active=True).count(),
        })
        return context


class AILearningGamesView(TemplateView):
    """AI Learning Games category page"""
    template_name = 'games/ai_learning.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'AI Learning Games - Train Your Robotic Buddy',
            'page_description': 'Interactive AI learning games where students create and train their own robotic buddies. Learn programming, machine learning, and problem-solving through hands-on AI education.',
            'activities': GameActivity.objects.filter(is_active=True)[:6],
            'buddy_count': RoboticBuddy.objects.count(),
        })
        return context


class RoboticBuddyLandingView(TemplateView):
    """Individual game landing - Robotic Buddy"""
    template_name = 'games/robotic_buddy_landing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Create Your AI Robotic Buddy - Interactive Learning Game',
            'page_description': 'Design, customize, and train your very own AI robotic buddy. Learn artificial intelligence concepts through fun, interactive training sessions and watch your buddy grow smarter.',
            'activities': GameActivity.objects.filter(is_active=True, activity_type='classification')[:3],
            'recent_buddies': RoboticBuddy.objects.order_by('-created_at')[:5],
        })
        return context


class SimpleGameLandingView(TemplateView):
    """Individual game landing - Simple Learning Game"""
    template_name = 'games/simple_game_landing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Simple AI Learning Game - Quick Training Sessions',
            'page_description': 'Fast-paced AI learning through simple classification games. Perfect introduction to machine learning concepts for young learners.',
        })
        return context


class DragDropGameLandingView(TemplateView):
    """Individual game landing - Drag & Drop Game"""
    template_name = 'games/drag_drop_game_landing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Drag & Drop AI Game - Visual Learning Interface',
            'page_description': 'Interactive drag-and-drop interface for teaching AI classification. Visual learning tool perfect for hands-on artificial intelligence education.',
        })
        return context


class GroupLearningGamesView(TemplateView):
    """Group Learning Games category page"""
    template_name = 'games/group_learning.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Group Learning Games - Collaborative Educational Scenarios',
            'page_description': 'Multi-player educational scenarios where students collaborate to solve real-world challenges. Experience role-playing games focused on climate change, problem-solving, and teamwork.',
            'games': Game.objects.filter(is_active=True),
            'featured_game': Game.objects.filter(is_active=True).first(),
        })
        return context


class MonsoonMayhemLandingView(TemplateView):
    """Individual game landing - Monsoon Mayhem"""
    template_name = 'games/monsoon_mayhem_landing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            monsoon_game = Game.objects.get(title__icontains='Monsoon')
        except Game.DoesNotExist:
            monsoon_game = Game.objects.filter(is_active=True).first()
        
        context.update({
            'page_title': 'Monsoon Mayhem - Climate Crisis Collaboration Game',
            'page_description': 'Lead flood response efforts in rural India. Collaborate as district officials, farmers, engineers, and school principals to save communities from climate disasters.',
            'game': monsoon_game,
        })
        return context


class StemChallengesView(TemplateView):
    """STEM Challenges category (coming soon)"""
    template_name = 'games/stem_challenges.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'STEM Challenges - Science & Engineering Games (Coming Soon)',
            'page_description': 'Interactive STEM challenges combining science, technology, engineering, and mathematics through engaging game-based learning experiences.',
        })
        return context


class LanguageAdventuresView(TemplateView):
    """Language Adventures category (coming soon)"""
    template_name = 'games/language_adventures.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Language Adventures - Interactive Language Learning (Coming Soon)',
            'page_description': 'Immersive language learning adventures through storytelling, role-playing, and cultural exploration games.',
        })
        return context
