from django.urls import path
from . import views

app_name = 'quest_ciq'

urlpatterns = [
    # Public views
    path('', views.home_view, name='home'),
    path('quest/<slug:quest_slug>/join/', views.join_quest_view, name='join'),
    path('quest/<slug:quest_slug>/level/<int:level_number>/', views.level_view, name='level'),
    path('quest/<slug:quest_slug>/summary/', views.summary_view, name='summary'),
    path('quest/<slug:quest_slug>/leaderboard/', views.leaderboard_view, name='leaderboard'),

    # Teacher views
    path('teacher/dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('teacher/quest/<slug:quest_slug>/facilitate/', views.facilitate_view, name='facilitate'),
]
