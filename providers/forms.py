from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import RecoveryProvider


class RecoveryProviderRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    company_name = forms.CharField(max_length=200)
    contact_person = forms.CharField(max_length=100)
    phone_number = forms.CharField(max_length=20)
    business_registration = forms.CharField(max_length=50)
    service_area = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            RecoveryProvider.objects.create(
                user=user,
                company_name=self.cleaned_data['company_name'],
                contact_person=self.cleaned_data['contact_person'],
                phone_number=self.cleaned_data['phone_number'],
                business_registration=self.cleaned_data['business_registration'],
                service_area=self.cleaned_data['service_area'],
                verification_status='pending',
            )
        return user