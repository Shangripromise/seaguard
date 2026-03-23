from django.urls import path
from . import views

app_name = 'vessels'

urlpatterns = [
    path('', views.vessel_list, name='vessel_list'),
    path('add/', views.vessel_add, name='vessel_add'),
    path('<int:pk>/', views.vessel_detail, name='vessel_detail'),
    path('<int:pk>/delete/', views.vessel_delete, name='vessel_delete'),
    path('<int:vessel_pk>/documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('<int:vessel_pk>/maintenance/', views.maintenance_request, name='maintenance_request'),
    path('maintenance/<int:pk>/', views.maintenance_detail, name='maintenance_detail'),
    path('<int:vessel_pk>/passage/create/', views.passage_plan_create, name='passage_plan_create'),
    path('passage/<int:pk>/', views.passage_plan_detail, name='passage_plan_detail'),
    path('passage/<int:pk>/edit/', views.passage_plan_edit, name='passage_plan_edit'),
    path('passage/<int:pk>/delete/', views.passage_plan_delete, name='passage_plan_delete'),
]
