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
    path('session/<str:session_code>/dashboard/', views.SessionDashboardView.as_view(), name='session_dashboard'),
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
    
    # Constitution Challenge URLs
    path('constitution/start/', views.ConstitutionQuickStartView.as_view(), name='constitution_quick_start'),
    path('constitution/start/<str:level>/', views.ConstitutionQuickStartView.as_view(), name='constitution_quick_start_level'),
    path('constitution/<str:session_code>/', views.ConstitutionTeamJoinView.as_view(), name='constitution_join'),
    path('constitution/<str:session_code>/play/', views.ConstitutionGameView.as_view(), name='constitution_game'),
    path('constitution/<str:session_code>/create-team/', views.ConstitutionTeamCreateView.as_view(), name='constitution_create_team'),
    
    # Constitution Challenge API endpoints
    path('api/constitution/<str:session_code>/question/', views.ConstitutionQuestionAPI.as_view(), name='constitution_question_api'),
    path('api/constitution/<str:session_code>/answer/', views.ConstitutionAnswerAPI.as_view(), name='constitution_answer_api'),
    path('api/constitution/<str:session_code>/leaderboard/', views.ConstitutionLeaderboardAPI.as_view(), name='constitution_leaderboard_api'),
    
    # Production setup endpoints
    path('api/test/', views.ProductionTestAPI.as_view(), name='production_test_api'),
    path('api/migrate/', views.ProductionMigrateAPI.as_view(), name='production_migrate_api'),
    path('api/diagnostics/', views.ProductionDiagnosticsAPI.as_view(), name='production_diagnostics_api'),
    path('api/setup-production/', views.ProductionSetupAPI.as_view(), name='production_setup_api'),
]