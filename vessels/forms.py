from django import forms
from .models import Vessel, VesselDocument, MaintenanceRequest, PassagePlan

class VesselForm(forms.ModelForm):
    class Meta:
        model = Vessel
        fields = ['name', 'imo_number', 'vessel_type', 'flag',
                  'call_sign', 'mmsi', 'ssr_number', 'description']

class VesselDocumentForm(forms.ModelForm):
    class Meta:
        model = VesselDocument
        fields = ['document_type', 'title', 'file', 'expiry_date', 'notes']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['check_type', 'description', 'requested_date']
        widgets = {
            'requested_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class PassagePlanForm(forms.ModelForm):
    class Meta:
        model = PassagePlan
        fields = [
            'title', 'departure_port', 'destination_port',
            'departure_datetime', 'estimated_arrival',
            'route_description', 'hazards', 'alternate_ports',
            'vhf_channels', 'tidal_notes', 'current_notes',
            'crew_list', 'persons_on_board',
            'check_bilge', 'check_engine_bilge', 'check_oil_level',
            'check_coolant', 'check_transmission',
            'engine_battery_v', 'service_battery_v',
            'fuel_level_pct', 'water_fwd_pct', 'water_aft_pct',
            'engine_hours_start',
            'weather_forecast', 'sea_state', 'notes',
        ]
        widgets = {
            'departure_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'estimated_arrival': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'route_description': forms.Textarea(attrs={'rows': 4}),
            'hazards': forms.Textarea(attrs={'rows': 3}),
            'alternate_ports': forms.Textarea(attrs={'rows': 2}),
            'tidal_notes': forms.Textarea(attrs={'rows': 3}),
            'current_notes': forms.Textarea(attrs={'rows': 2}),
            'crew_list': forms.Textarea(attrs={'rows': 3}),
            'weather_forecast': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
