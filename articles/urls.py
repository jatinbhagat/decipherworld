from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='article_list'),
    path('<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),
    
    # Comment management (AJAX endpoints)
    path('<slug:slug>/comment/add/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    # Like system (AJAX endpoint)
    path('<slug:slug>/like/', views.toggle_like, name='toggle_like'),
    
    # Share tracking (AJAX endpoint)
    path('<slug:slug>/share/', views.track_share, name='track_share'),
]