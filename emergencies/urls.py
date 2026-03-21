from django.urls import path
from . import views

app_name = 'emergencies'

urlpatterns = [
    # Existing
    path('', views.emergency_list, name='emergency_list'),
    path('submit/', views.emergency_submit, name='emergency_submit'),
    path('<int:pk>/', views.emergency_detail, name='emergency_detail'),
    path('<int:pk>/update-status/', views.update_status, name='update_status'),

    # CR5 — Admin monitoring dashboard
    path('admin/jobs/', views.admin_job_dashboard, name='admin_job_dashboard'),
    path('admin/jobs/<int:pk>/assign/', views.admin_assign_provider, name='admin_assign'),
    path('admin/jobs/<int:pk>/escalate/', views.admin_escalate, name='admin_escalate'),
]