from django.urls import path
from . import views, climate_views

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
    path('constitution/<str:session_code>/final-results/', views.ConstitutionFinalResultsView.as_view(), name='constitution_final_results'),
    path('constitution/<str:session_code>/feedback/', views.ConstitutionFeedbackView.as_view(), name='submit_constitution_feedback'),
    
    # Constitution Challenge API endpoints
    path('api/constitution/<str:session_code>/question/', views.ConstitutionQuestionAPI.as_view(), name='constitution_question_api'),
    path('api/constitution/<str:session_code>/answer/', views.ConstitutionAnswerAPI.as_view(), name='constitution_answer_api'),
    path('api/constitution/<str:session_code>/leaderboard/', views.ConstitutionLeaderboardAPI.as_view(), name='constitution_leaderboard_api'),
    
    # Climate Change Simulation Game URLs
    path('climate/', climate_views.climate_game_home, name='climate_game_home'),
    path('climate/create/', climate_views.create_climate_session, name='create_climate_session'),
    path('climate/join/<str:session_code>/', climate_views.join_climate_session, name='join_climate_session'),
    path('climate/<str:session_code>/dashboard/', climate_views.climate_facilitator_dashboard, name='climate_facilitator_dashboard'),
    path('climate/<str:session_code>/lobby/', climate_views.climate_game_lobby, name='climate_game_lobby'),
    path('climate/<str:session_code>/play/', climate_views.climate_game_play, name='climate_game_play'),
    path('climate/<str:session_code>/impact-results/', climate_views.climate_impact_results, name='climate_impact_results'),
    
    # Testing URLs for development
    path('climate/test/create/', climate_views.create_test_climate_session, name='create_test_climate_session'),
    path('climate/test/<str:session_code>/', climate_views.quick_test_join, name='quick_test_join'),
    path('climate/test/<str:session_code>/<str:role>/', climate_views.quick_test_join, name='quick_test_join_role'),
    
    # Climate Game API endpoints
    path('api/climate/<str:session_code>/start/', climate_views.start_climate_game, name='start_climate_game'),
    path('api/climate/<str:session_code>/advance/', climate_views.advance_climate_phase, name='advance_climate_phase'),
    path('api/climate/<str:session_code>/status/', climate_views.get_climate_session_status, name='get_climate_session_status'),
    
    # Timer API endpoints
    path('api/climate/<str:session_code>/timer/set/', climate_views.set_timer_duration, name='set_timer_duration'),
    path('api/climate/<str:session_code>/timer/start/', climate_views.start_round_timer, name='start_round_timer'),
    path('api/climate/<str:session_code>/timer/status/', climate_views.get_timer_status, name='get_timer_status'),
    
    # Production setup endpoints
    path('api/test/', views.ProductionTestAPI.as_view(), name='production_test_api'),
    path('api/migrate/', views.ProductionMigrateAPI.as_view(), name='production_migrate_api'),
    path('api/diagnostics/', views.ProductionDiagnosticsAPI.as_view(), name='production_diagnostics_api'),
    path('api/setup-production/', views.ProductionSetupAPI.as_view(), name='production_setup_api'),
    
    # Design Thinking / Classroom Innovators Challenge URLs
    path('design-thinking/', views.DesignThinkingStartView.as_view(), name='design_thinking_start'),
    path('design-thinking/create/', views.DesignThinkingCreateView.as_view(), name='design_thinking_create'),
    path('design-thinking/join/', views.DesignThinkingJoinView.as_view(), name='design_thinking_join'),
    path('design-thinking/<str:session_code>/facilitator/', views.DesignThinkingFacilitatorView.as_view(), name='design_thinking_facilitator'),
    path('design-thinking/<str:session_code>/play/', views.DesignThinkingPlayView.as_view(), name='design_thinking_play'),
    
    # Design Thinking API endpoints
    path('api/design-thinking/<str:session_code>/submit/', views.DesignThinkingSubmissionAPI.as_view(), name='design_thinking_submit'),
    path('api/design-thinking/<str:session_code>/control/', views.DesignThinkingMissionControlAPI.as_view(), name='design_thinking_control'),
    path('api/design-thinking/<str:session_code>/status/', views.DesignThinkingStatusAPI.as_view(), name='design_thinking_status'),
    path('session/<str:session_code>/mission-interface/', views.DesignThinkingMissionInterfaceAPI.as_view(), name='design_thinking_mission_interface'),
]