from django.urls import path
from . import views

app_name = 'providers'

urlpatterns = [
    path('register/', views.provider_register, name='register'),
    path('list/', views.provider_list, name='list'),
    path('<int:provider_id>/', views.provider_detail, name='detail'),
    path('pending/', views.pending_approval, name='pending_approval'),
    path('dashboard/', views.provider_dashboard, name='dashboard'),
    path('admin/review/', views.admin_provider_review, name='admin_review'),
    path('admin/approve/<int:provider_id>/', views.admin_provider_approve, name='approve'),
    path('admin/reject/<int:provider_id>/', views.admin_provider_reject, name='reject'),
]