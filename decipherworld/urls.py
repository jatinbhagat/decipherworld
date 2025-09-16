from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic import RedirectView
from core.views_robots import robots_txt
from core.sitemap_views import simple_sitemap

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', simple_sitemap, name='sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico', permanent=True)),
    path('', include('core.urls')),
    path('games/', include('games.urls')),
    path('cyber-city/', include('cyber_city.urls')),
    
    # Keep the apps but they're now accessed through games/ namespace
    # These are needed for internal template references
    path('buddy/', include('robotic_buddy.urls')),
    path('learn/', include('group_learning.urls')),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)