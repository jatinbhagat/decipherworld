from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.about, name='about'),
    path('courses/', views.CoursesView.as_view(), name='courses'),
    path('teachers/', views.TeachersView.as_view(), name='teachers'),
    path('schools/', views.SchoolsView.as_view(), name='schools'),
    path('school-presentation/', views.SchoolPresentationView.as_view(), name='school-presentation'),
    path('gallery/', views.GalleryView.as_view(), name='gallery'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('migrate/', views.run_migrations, name='migrate'),
    path('migrate-robotic-buddy/', views.migrate_robotic_buddy, name='migrate_robotic_buddy'),
    path('check-robotic-buddy/', views.check_robotic_buddy, name='check_robotic_buddy'),
    path('populate-cyber-challenges/', views.populate_cyber_challenges, name='populate_cyber_challenges'),
    path('populate-cyberbully-challenges/', views.populate_cyberbully_challenges_web, name='populate_cyberbully_challenges'),
    path('run-production-migrations/', views.run_production_migrations, name='run_production_migrations'),
    path('fix-migration-conflicts/', views.fix_migration_conflicts, name='fix_migration_conflicts'),
    path('submit-game-review/', views.submit_game_review, name='submit_game_review'),
]