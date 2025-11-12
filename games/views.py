from django.shortcuts import render
from django.views.generic import TemplateView
from group_learning.models import Game
from robotic_buddy.models import RoboticBuddy, GameActivity
from core.analytics import track_page_view


class GamesHubView(TemplateView):
    """Main Games Hub - Overview of all game categories"""
    template_name = 'games/hub.html'
    
    def get(self, request, *args, **kwargs):
        # Track games hub page view
        track_page_view(request, 'Games Hub', {
            'page_category': 'Games',
            'is_main_hub': True
        })
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Educational Games Hub - Game Based Learning for CBSE ICSE Students | DecipherWorld India',
            'page_description': 'Discover AI learning games, cyber security training, and constitutional challenges for CBSE & ICSE students across India. Interactive game-based learning platform for grades 1-10.',
            'canonical_url': '/games/',
            'group_learning_count': Game.objects.filter(is_active=True).count(),
            'robotic_buddy_count': RoboticBuddy.objects.count(),
            # Include core AI games (Robotic Buddy, Simple Game, Emotion Game, Drag & Drop) + dynamic activities
            'ai_activities_count': 4 + GameActivity.objects.filter(is_active=True).count(),
        })
        return context


class AILearningGamesView(TemplateView):
    """AI Learning Games category page"""
    template_name = 'games/ai_learning.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'AI Learning Games for Kids - Grades 1-5 | Machine Learning Education India',
            'page_description': 'Interactive AI and machine learning games for CBSE ICSE students grades 1-5. Create robotic buddies, learn artificial intelligence through fun educational games across India.',
            'canonical_url': '/games/ai-learning/',
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
            'page_title': 'Create AI Robotic Buddy - Personalized Learning Companion for Kids | DecipherWorld',
            'page_description': 'Build your own AI robotic buddy! Personalized learning companion for CBSE ICSE students. Create, customize, and learn with your AI friend through interactive games.',
            'canonical_url': '/games/ai-learning/robotic-buddy/',
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
            'page_title': 'Simple AI Learning Game - Introduction to Machine Learning for Kids | DecipherWorld',
            'page_description': 'Start your AI journey with our simple learning game. Perfect introduction to artificial intelligence and machine learning for CBSE ICSE students grades 1-6.',
            'canonical_url': '/games/ai-learning/simple-game/',
        })
        return context


class DragDropGameLandingView(TemplateView):
    """Individual game landing - Drag & Drop Game"""
    template_name = 'games/drag_drop_game_landing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Drag & Drop AI Classification Game - Interactive Machine Learning for Kids | DecipherWorld',
            'page_description': 'Learn AI classification through fun drag-and-drop gameplay. Interactive machine learning game for CBSE ICSE students grades 1-8. Teach artificial intelligence concepts visually.',
            'canonical_url': '/games/ai-learning/drag-drop-game/',
        })
        return context


class GroupLearningGamesView(TemplateView):
    """Group Learning Games category page"""
    template_name = 'games/group_learning.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Group Learning Games - Collaborative Educational Scenarios | DecipherWorld',
            'page_description': 'Multi-player educational scenarios where students collaborate to solve real-world challenges. Experience role-playing games focused on climate change, problem-solving, and teamwork.',
            'canonical_url': '/games/group-learning/',
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
            'page_title': 'Monsoon Mayhem - Climate Crisis Collaboration Game | DecipherWorld',
            'page_description': 'Lead flood response efforts in rural India. Collaborate as district officials, farmers, engineers, and school principals to save communities from climate disasters.',
            'canonical_url': '/games/group-learning/monsoon-mayhem/',
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


class CyberSecurityGamesView(TemplateView):
    """Cyber Security Games category page"""
    template_name = 'games/cyber_security.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Cyber Security Games for Kids - Digital Safety Education India | Grades 1-6',
            'page_description': 'Learn cyber security through interactive games for CBSE ICSE students grades 1-6. Password safety, digital threats, and online protection training across India.',
            'canonical_url': '/games/cyber-security/',
        })
        return context


class ConstitutionBasicView(TemplateView):
    """Constitution Basic Games category page"""
    template_name = 'games/constitution_basic.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Constitution Learning Games - Indian Civics for CBSE ICSE Grades 4-7 | Team Games',
            'page_description': 'Learn Indian Constitution through team-based civics games for CBSE ICSE students grades 4-7. Democratic principles, fundamental rights, and governance education across India.',
            'canonical_url': '/games/constitution-basic/',
        })
        return context


class ConstitutionAdvancedView(TemplateView):
    """Constitution Advanced Games category page"""
    template_name = 'games/constitution_advanced.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Advanced Constitution Games - Indian Constitutional Law | CBSE ICSE Grades 7-10',
            'page_description': 'Master Indian Constitutional law through advanced team games for CBSE ICSE students grades 7-10. Supreme Court cases, constitutional analysis, and legal reasoning education.',
            'canonical_url': '/games/constitution-advanced/',
        })
        return context


class FinancialLiteracyView(TemplateView):
    """Financial Literacy Games category page"""
    template_name = 'games/financial_literacy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Financial Literacy Games - Budgeting Banking Investment | CBSE ICSE Grades 5-10',
            'page_description': 'Learn budgeting, banking, stocks and mutual funds through interactive games for CBSE ICSE students grades 5-10. CBSE curriculum aligned financial decision-making education across India.',
            'canonical_url': '/games/financial-literacy/',
        })
        return context


class EntrepreneurshipView(TemplateView):
    """Entrepreneurship Games category page"""
    template_name = 'games/entrepreneurship.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Entrepreneurship Games - Business Building Team Challenges | CBSE ICSE Grades 4-10',
            'page_description': 'Build on Lemonade Stand Game to teach business basics through team collaboration for CBSE ICSE students grades 4-10. Business planning, strategy, and scaling education across India.',
            'canonical_url': '/games/entrepreneurship/',
        })
        return context


class DesignThinkingQuestView(TemplateView):
    """Design Thinking Quest landing page"""
    template_name = 'games/design_thinking_quest.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Design Thinking Quest - Innovation Challenge for Students | CBSE ICSE Grades 6-12',
            'page_description': 'Complete the 5-level design thinking journey: Empathy → Define → Ideate → Prototype → Test. Available in both individual and team modes for CBSE ICSE students.',
            'canonical_url': '/games/design-thinking-quest/',
        })
        return context
