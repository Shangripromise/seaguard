from django import forms
from .models import EmergencyRequest, StatusUpdate
from vessels.models import Vessel


class EmergencyRequestForm(forms.ModelForm):
    class Meta:
        model  = EmergencyRequest
        fields = ['vessel', 'emergency_type', 'description', 'latitude', 'longitude']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vessel'].queryset = Vessel.objects.filter(owner=user)


class StatusUpdateForm(forms.ModelForm):
    new_status = forms.ChoiceField(choices=[], label='New status')

    class Meta:
        model   = StatusUpdate
        fields  = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional notes…'}),
        }

    def __init__(self, *args, allowed_transitions=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_transitions:
            self.fields['new_status'].choices = allowed_transitions