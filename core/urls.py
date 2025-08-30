from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('courses/', views.CoursesView.as_view(), name='courses'),
    path('teachers/', views.TeachersView.as_view(), name='teachers'),
    path('contact/', views.ContactView.as_view(), name='contact'),
]