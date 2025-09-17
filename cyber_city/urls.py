
from django.urls import path
from . import views

app_name = 'cyber_city'

urlpatterns = [
    # Mission Selection Hub (no session needed)
    path('', views.CyberCityMissionHubView.as_view(), name='mission_hub'),
    
    # Quick game creation for missions
    path('start/', views.CyberCityQuickGameView.as_view(), name='quick_game'),
    
    # Mission 1: Password Fortress
    path('<str:session_code>/password-fortress/', views.PasswordFortressView.as_view(), name='password_fortress'),
    
    # Mission 2: Cyberbully Crisis
    path('<str:session_code>/cyberbully-crisis/', views.CyberbullyCrisisView.as_view(), name='cyberbully_crisis'),
    
    # Common URLs
    path('<str:session_code>/avatar/', views.CyberCityAvatarView.as_view(), name='avatar'),
    path('<str:session_code>/action/', views.CyberCityActionAPI.as_view(), name='action'),
]
