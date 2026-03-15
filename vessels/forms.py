from django import forms
from .models import Vessel


class VesselForm(forms.ModelForm):
    class Meta:
        model = Vessel
        fields = ['name', 'imo_number', 'vessel_type', 'flag']
        