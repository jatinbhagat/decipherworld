from django.urls import path, include
from . import views

app_name = 'games'

urlpatterns = [
    # Main Games Hub
    path('', views.GamesHubView.as_view(), name='hub'),
    
    # AI Learning Games section
    path('ai-learning/', views.AILearningGamesView.as_view(), name='ai_learning'),
    path('ai-learning/robotic-buddy/', views.RoboticBuddyLandingView.as_view(), name='robotic_buddy_landing'),
    path('ai-learning/simple-game/', views.SimpleGameLandingView.as_view(), name='simple_game_landing'),
    path('ai-learning/drag-drop-game/', views.DragDropGameLandingView.as_view(), name='drag_drop_game_landing'),
    
    # Group Learning Games section
    path('group-learning/', views.GroupLearningGamesView.as_view(), name='group_learning'),
    path('group-learning/monsoon-mayhem/', views.MonsoonMayhemLandingView.as_view(), name='monsoon_mayhem_landing'),
    
    # Future game categories
    path('stem-challenges/', views.StemChallengesView.as_view(), name='stem_challenges'),
    path('language-adventures/', views.LanguageAdventuresView.as_view(), name='language_adventures'),
    
    # Include existing games under games/ namespace
    path('buddy/', include('robotic_buddy.urls')),
    path('learn/', include('group_learning.urls')),
]