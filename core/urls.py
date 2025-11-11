from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('test-home/', views.simple_home_test, name='test_home'),
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.about, name='about'),
    path('courses/', views.CoursesView.as_view(), name='courses'),
    path('teachers/', views.TeachersView.as_view(), name='teachers'),
    path('students/', views.StudentsView.as_view(), name='students'),
    path('schools/', views.SchoolsView.as_view(), name='schools'),
    path('school-presentation/', views.SchoolPresentationView.as_view(), name='school-presentation'),
    path('gallery/', views.GalleryView.as_view(), name='gallery'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('school-referral/', views.SchoolReferralView.as_view(), name='school_referral'),
    path('school-referral/success/', views.school_referral_success, name='school_referral_success'),
    path('upload-schools-csv/', views.upload_schools_csv, name='upload_schools_csv'),
    path('migrate/', views.run_migrations, name='migrate'),
    path('migrate-robotic-buddy/', views.migrate_robotic_buddy, name='migrate_robotic_buddy'),
    path('check-robotic-buddy/', views.check_robotic_buddy, name='check_robotic_buddy'),
    path('populate-cyber-challenges/', views.populate_cyber_challenges, name='populate_cyber_challenges'),
    path('populate-cyberbully-challenges/', views.populate_cyberbully_challenges_web, name='populate_cyberbully_challenges'),
    path('run-production-migrations/', views.run_production_migrations, name='run_production_migrations'),
    path('fix-migration-conflicts/', views.fix_migration_conflicts, name='fix_migration_conflicts'),
    path('create-sample-courses/', views.create_sample_courses, name='create_sample_courses'),
    path('submit-game-review/', views.submit_game_review, name='submit_game_review'),
    path('create-production-superuser/', views.create_production_superuser, name='create_production_superuser'),
    path('mixpanel-test/', views.mixpanel_test, name='mixpanel_test'),
    path('health/', views.health_check, name='health_check'),
    path('api/track-event/', views.track_event_fallback, name='track_event_fallback'),
    path('api/analytics/track/', views.analytics_track_api, name='analytics_track_api'),
    path('migrate-quest-ciq/', views.migrate_quest_ciq, name='migrate_quest_ciq'),
    path('clean-test-data/', views.clean_production_test_data, name='clean_test_data'),
    path('setup-quest-ciq-data/', views.setup_quest_ciq_data, name='setup_quest_ciq_data'),
]