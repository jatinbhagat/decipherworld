"""
URLs for Classroom Innovation Quest
"""
from django.urls import path
from . import views

app_name = 'quest_ciq'

urlpatterns = [
    # Home and join
    path('', views.HomeView.as_view(), name='home'),
    path('join/', views.JoinQuestView.as_view(), name='join'),

    # Quest levels
    path('quest/<str:session_code>/level/<int:level_order>/', views.LevelView.as_view(), name='level'),

    # Progress and leaderboard
    path('quest/<str:session_code>/progress/', views.ProgressView.as_view(), name='progress'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),

    # Public team presentation (read-only)
    path('quest/<slug:slug>/present/<str:class_code>/<slug:team_slug>/',
         views.PublicPresentationView.as_view(), name='public_presentation'),

    # Teacher grading
    path('teacher/<str:class_code>/grade/',
         views.TeacherGradeView.as_view(), name='teacher_grade'),
]
