from django.urls import path
from . import views

app_name = 'robotic_buddy'

urlpatterns = [
    # Main game entry points
    path('', views.GameHomeView.as_view(), name='home'),
    path('create-buddy/', views.CreateBuddyView.as_view(), name='create_buddy'),
    path('my-buddy/', views.MyBuddyView.as_view(), name='my_buddy'),
    
    # Training Activities
    path('activities/', views.ActivitiesView.as_view(), name='activities'),
    path('activity/<int:activity_id>/', views.ActivityDetailView.as_view(), name='activity_detail'),
    path('training/<int:activity_id>/', views.TrainingSessionView.as_view(), name='training_session'),
    
    # Classification Game (our first MVP feature)
    path('classification-game/', views.ClassificationGameView.as_view(), name='classification_game'),
    path('simple-game/', views.SimpleGameView.as_view(), name='simple_game'),
    
    # AJAX endpoints for game interactions
    path('api/submit-example/', views.submit_training_example, name='submit_example'),
    path('api/buddy-prediction/', views.get_buddy_prediction, name='buddy_prediction'),
    path('api/complete-session/', views.complete_training_session, name='complete_session'),
    
    # Progress and Stats
    path('buddy-stats/', views.BuddyStatsView.as_view(), name='buddy_stats'),
    path('achievements/', views.AchievementsView.as_view(), name='achievements'),
]