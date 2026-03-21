from django.urls import path
from . import views

app_name = 'providers'

urlpatterns = [
    # Existing
    path('register/', views.provider_register, name='register'),
    path('list/', views.provider_list, name='list'),
    path('<int:provider_id>/', views.provider_detail, name='detail'),
    path('pending/', views.pending_approval, name='pending_approval'),
    path('dashboard/', views.provider_dashboard, name='dashboard'),
    path('admin/review/', views.admin_provider_review, name='admin_review'),
    path('admin/approve/<int:provider_id>/', views.admin_provider_approve, name='approve'),
    path('admin/reject/<int:provider_id>/', views.admin_provider_reject, name='reject'),

    # CR1 — Advanced search / filter on provider directory
    path('search/', views.provider_search, name='search'),

    # CR4 — Admin rating moderation queue
    path('admin/ratings/', views.admin_rating_moderation, name='admin_rating_moderation'),
    path('admin/ratings/<int:rating_id>/approve/', views.admin_rating_approve, name='rating_approve'),
    path('admin/ratings/<int:rating_id>/reject/', views.admin_rating_reject, name='rating_reject'),
]