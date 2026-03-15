from django.db import models
from django.contrib.auth.models import User


class Vessel(models.Model):
    VESSEL_TYPES = [
        ('cargo', 'Cargo Ship'),
        ('tanker', 'Tanker'),
        ('passenger', 'Passenger Ship'),
        ('fishing', 'Fishing Vessel'),
        ('tug', 'Tug Boat'),
        ('other', 'Other'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vessels')
    name = models.CharField(max_length=100)
    imo_number = models.CharField(max_length=20, unique=True)
    vessel_type = models.CharField(max_length=20, choices=VESSEL_TYPES)
    flag = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} ({self.imo_number})'
    