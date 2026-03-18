from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('vessels/', include('vessels.urls', namespace='vessels')),
    path('emergencies/', include('emergencies.urls', namespace='emergencies')),
    path('providers/', include('providers.urls', namespace='providers')),
]