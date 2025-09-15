
from django.urls import path
from . import views

app_name = 'cyber_city'

urlpatterns = [
    # Quick game creation (no session code needed)
    path('', views.CyberCityQuickGameView.as_view(), name='quick_game'),
    
    # Game session URLs
    path('<str:session_code>/', views.CyberCityGameView.as_view(), name='game'),
    path('<str:session_code>/avatar/', views.CyberCityAvatarView.as_view(), name='avatar'),
    path('<str:session_code>/action/', views.CyberCityActionAPI.as_view(), name='action'),
]
