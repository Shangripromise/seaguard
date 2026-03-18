from django.urls import path
from . import views
app_name = 'emergencies'


urlpatterns = [
    path('', views.emergency_list, name='emergency_list'),
    path('submit/', views.emergency_submit, name='emergency_submit'),
    path('<int:pk>/', views.emergency_detail, name='emergency_detail'),
]