from django.urls import path
from . import views

app_name = 'group_learning'

urlpatterns = [
    # Game selection and session creation
    path('', views.GameListView.as_view(), name='game_list'),
    path('game/<int:pk>/', views.GameDetailView.as_view(), name='game_detail'),
    
    # Session management
    path('session/create/<int:game_id>/', views.CreateSessionView.as_view(), name='create_session'),
    path('session/<str:session_code>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('session/<str:session_code>/join/', views.JoinSessionView.as_view(), name='join_session'),
    
    # Gameplay
    path('play/<str:session_code>/', views.GameplayView.as_view(), name='gameplay'),
    path('play/<str:session_code>/action/', views.PlayerActionView.as_view(), name='player_action'),
    
    # Results and reflection
    path('session/<str:session_code>/results/', views.SessionResultsView.as_view(), name='session_results'),
    path('session/<str:session_code>/reflection/', views.ReflectionView.as_view(), name='reflection'),
    
    # AJAX endpoints
    path('api/session/<str:session_code>/status/', views.SessionStatusAPI.as_view(), name='session_status_api'),
    path('api/session/<str:session_code>/actions/', views.SessionActionsAPI.as_view(), name='session_actions_api'),
]