from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('vessels/', include('vessels.urls')),
    path('emergencies/', include('emergencies.urls')),
    path('providers/', include('providers.urls', namespace='providers')),
]