from django.db import models
from django.contrib.auth.models import User
from vessels.models import Vessel


class EmergencyRequest(models.Model):
    STATUS_CHOICES = [
        ('active',    'Active'),
        ('resolved',  'Resolved'),
        ('cancelled', 'Cancelled'),
    ]

    EMERGENCY_TYPES = [
        ('fire',          'Fire'),
        ('flooding',      'Flooding'),
        ('medical',       'Medical Emergency'),
        ('collision',     'Collision'),
        ('grounding',     'Grounding'),
        ('man_overboard', 'Man Overboard'),
        ('other',         'Other'),
    ]

    TRANSITIONS = {
        'active':    {'resolved':  ['provider', 'staff'],
                      'cancelled': ['provider', 'staff']},
        'resolved':  {'active':    ['provider', 'staff']},
        'cancelled': {},
    }

    vessel         = models.ForeignKey(Vessel, on_delete=models.CASCADE)
    submitted_by   = models.ForeignKey(User, on_delete=models.CASCADE)
    emergency_type = models.CharField(max_length=20, choices=EMERGENCY_TYPES)
    description    = models.TextField()
    latitude       = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude      = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at     = models.DateTimeField(auto_now_add=True)

    def allowed_transitions(self, user):
        role = 'staff' if user.is_staff else 'provider'
        transitions = self.TRANSITIONS.get(self.status, {})
        allowed = []
        for next_status, roles in transitions.items():
            if role in roles:
                label = dict(self.STATUS_CHOICES).get(next_status, next_status)
                allowed.append((next_status, label))
        return allowed

    def __str__(self):
        return f'{self.emergency_type} - {self.vessel.name} ({self.created_at})'


class StatusUpdate(models.Model):
    emergency   = models.ForeignKey(EmergencyRequest, on_delete=models.CASCADE, related_name='status_updates')
    changed_by  = models.ForeignKey(User, on_delete=models.CASCADE)
    from_status = models.CharField(max_length=20)
    to_status   = models.CharField(max_length=20)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'#{self.emergency.pk}: {self.from_status} → {self.to_status}'