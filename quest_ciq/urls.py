"""
URL configuration for quest_ciq app.
"""
from django.urls import path
from . import views

app_name = 'quest_ciq'

urlpatterns = [
    # Quest routes with slug
    path('quest/<slug:slug>/', views.quest_home, name='quest_home'),
    path('quest/<slug:slug>/join/', views.quest_join, name='quest_join'),
    path('quest/<slug:slug>/level/<int:order>/', views.quest_level, name='quest_level'),
    path('quest/<slug:slug>/summary/', views.quest_summary, name='quest_summary'),
    path('quest/<slug:slug>/leaderboard/', views.quest_leaderboard, name='quest_leaderboard'),
    path('quest/<slug:slug>/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('quest/<slug:slug>/facilitate/', views.facilitate, name='facilitate'),
]
