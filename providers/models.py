from django.db import models
from django.contrib.auth.models import User


class RecoveryProvider(models.Model):

    VERIFICATION_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    business_registration = models.CharField(max_length=50)
    service_area = models.CharField(max_length=200)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.company_name} ({self.verification_status})'