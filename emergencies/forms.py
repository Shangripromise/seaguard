from django import forms
from .models import EmergencyRequest
from vessels.models import Vessel


class EmergencyRequestForm(forms.ModelForm):
    class Meta:
        model = EmergencyRequest
        fields = ['vessel', 'emergency_type', 'description', 'latitude', 'longitude']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vessel'].queryset = Vessel.objects.filter(owner=user)
        