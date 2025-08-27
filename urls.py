from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('courses/', views.courses, name='courses'),
    path('teachers/', views.teachers, name='teachers'),
    path('contact/', views.contact, name='contact'),
    path('signup/', views.signup, name='signup'),  # Implement signup view
    path('coming-soon/', views.coming_soon, name='coming_soon'),
]