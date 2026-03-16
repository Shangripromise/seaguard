from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('vessels/', include('vessels.urls')),
    path('emergencies/', include('emergencies.urls')),
    path('', RedirectView.as_view(url='/accounts/login/')),
]