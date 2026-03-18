from django.contrib import admin
from .models import Vessel


@admin.register(Vessel)
class VesselAdmin(admin.ModelAdmin):
    list_display  = ['name', 'imo_number', 'vessel_type', 'owner']
    search_fields = ['name', 'imo_number', 'owner__username']