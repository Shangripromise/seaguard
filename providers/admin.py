from django.contrib import admin
from .models import RecoveryProvider, ProviderRating


@admin.register(RecoveryProvider)
class RecoveryProviderAdmin(admin.ModelAdmin):
    list_display  = ['company_name', 'contact_person', 'verification_status', 'created_at']
    list_filter   = ['verification_status']
    search_fields = ['company_name', 'user__username']


@admin.register(ProviderRating)
class ProviderRatingAdmin(admin.ModelAdmin):
    list_display  = ['provider', 'rated_by', 'score', 'created_at']
    list_filter   = ['score']
    readonly_fields = ['provider', 'rated_by', 'score', 'comment', 'created_at']