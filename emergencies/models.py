from django.db import models
from django.contrib.auth.models import User
from vessels.models import Vessel


class EmergencyRequest(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ]

    EMERGENCY_TYPES = [
        ('fire', 'Fire'),
        ('flooding', 'Flooding'),
        ('medical', 'Medical Emergency'),
        ('collision', 'Collision'),
        ('grounding', 'Grounding'),
        ('man_overboard', 'Man Overboard'),
        ('other', 'Other'),
    ]

    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    emergency_type = models.CharField(max_length=20, choices=EMERGENCY_TYPES)
    description = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.emergency_type} - {self.vessel.name} ({self.created_at})'