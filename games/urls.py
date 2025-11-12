from django.urls import path, include
from . import views

app_name = 'games'

urlpatterns = [
    # Main Games Hub
    path('', views.GamesHubView.as_view(), name='hub'),
    
    # AI Learning Games section (Grades 1-5, Individual)
    path('ai-learning/', views.AILearningGamesView.as_view(), name='ai_learning'),
    path('ai-learning/robotic-buddy/', views.RoboticBuddyLandingView.as_view(), name='robotic_buddy_landing'),
    path('ai-learning/simple-game/', views.SimpleGameLandingView.as_view(), name='simple_game_landing'),
    path('ai-learning/drag-drop-game/', views.DragDropGameLandingView.as_view(), name='drag_drop_game_landing'),
    
    # Cyber Security Games section (Grades 1-6, Individual)
    path('cyber-security/', views.CyberSecurityGamesView.as_view(), name='cyber_security'),
    
    # Financial Literacy Games section (Grades 5-10, Individual)
    path('financial-literacy/', views.FinancialLiteracyView.as_view(), name='financial_literacy'),
    
    # Constitution Basic (Grades 4-7, Team)
    path('constitution-basic/', views.ConstitutionBasicView.as_view(), name='constitution_basic'),
    
    # Constitution Advanced (Grades 7-10, Team)
    path('constitution-advanced/', views.ConstitutionAdvancedView.as_view(), name='constitution_advanced'),
    
    # Entrepreneurship Games section (Grades 4-10, Team)
    path('entrepreneurship/', views.EntrepreneurshipView.as_view(), name='entrepreneurship'),
    
    # Design Thinking Quest (Grades 6-12, Individual & Team)
    path('design-thinking-quest/', views.DesignThinkingQuestView.as_view(), name='design_thinking_quest'),
    
    # Legacy Group Learning redirect (for climate games like Monsoon Mayhem)
    path('group-learning/', views.GroupLearningGamesView.as_view(), name='group_learning'),
    path('group-learning/monsoon-mayhem/', views.MonsoonMayhemLandingView.as_view(), name='monsoon_mayhem_landing'),
    
    # Future game categories
    path('stem-challenges/', views.StemChallengesView.as_view(), name='stem_challenges'),
    path('language-adventures/', views.LanguageAdventuresView.as_view(), name='language_adventures'),
    
]