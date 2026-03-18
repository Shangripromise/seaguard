from django.urls import path
from . import views
app_name = 'vessels'

urlpatterns = [
    path('', views.vessel_list, name='vessel_list'),
    path('add/', views.vessel_add, name='vessel_add'),
    path('<int:pk>/', views.vessel_detail, name='vessel_detail'),
    path('<int:pk>/delete/', views.vessel_delete, name='vessel_delete'),
]