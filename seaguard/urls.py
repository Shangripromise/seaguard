from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/accounts/dashboard/'), name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('vessels/', include('vessels.urls', namespace='vessels')),
    path('emergencies/', include('emergencies.urls', namespace='emergencies')),
    path('providers/', include('providers.urls', namespace='providers')),
]