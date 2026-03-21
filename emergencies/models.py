from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from vessels.models import Vessel


class EmergencyRequest(models.Model):
    STATUS_CHOICES = [
        ('reported',  'Reported'),
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

    # Role-based status transitions
    # 'reported' is the initial state — unassigned, awaiting dispatch
    # 'active'   means a provider has been assigned and is responding
    TRANSITIONS = {
        'reported':  {
            'active':    ['staff'],
            'cancelled': ['provider', 'staff'],
        },
        'active':    {
            'resolved':  ['provider', 'staff'],
            'cancelled': ['provider', 'staff'],
        },
        'resolved':  {
            'active':    ['staff'],
        },
        'cancelled': {},
    }

    vessel            = models.ForeignKey(Vessel, on_delete=models.CASCADE)
    submitted_by      = models.ForeignKey(
                            User, on_delete=models.CASCADE,
                            related_name='submitted_emergencies'
                        )
    # CR2 / CR5 — which provider is currently assigned
    assigned_provider = models.ForeignKey(
                            'providers.RecoveryProvider',
                            on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='assigned_emergencies'
                        )
    emergency_type    = models.CharField(max_length=20, choices=EMERGENCY_TYPES)
    description       = models.TextField()
    latitude          = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude         = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    created_at        = models.DateTimeField(auto_now_add=True)
    # CR5 — track when something became unassigned for the >10 min red flag
    last_status_change = models.DateTimeField(default=timezone.now)

    def allowed_transitions(self, user):
        role = 'staff' if user.is_staff else 'provider'
        transitions = self.TRANSITIONS.get(self.status, {})
        allowed = []
        for next_status, roles in transitions.items():
            if role in roles:
                label = dict(self.STATUS_CHOICES).get(next_status, next_status)
                allowed.append((next_status, label))
        return allowed

    def minutes_since_last_change(self):
        """Used by CR5 dashboard to colour-code unassigned emergencies."""
        delta = timezone.now() - self.last_status_change
        return int(delta.total_seconds() / 60)

    def dashboard_colour(self):
        """
        Returns a Bootstrap colour string for CR5 admin dashboard.
        Green  = active with provider assigned
        Amber  = reported, waiting, under 10 min
        Red    = reported, waiting, over 10 min
        Grey   = resolved or cancelled
        """
        if self.status in ('resolved', 'cancelled'):
            return 'secondary'
        if self.status == 'active' and self.assigned_provider:
            return 'success'
        if self.minutes_since_last_change() > 10:
            return 'danger'
        return 'warning'

    def __str__(self):
        return f'{self.emergency_type} - {self.vessel.name} ({self.created_at})'


class StatusUpdate(models.Model):
    emergency   = models.ForeignKey(
                      EmergencyRequest, on_delete=models.CASCADE,
                      related_name='status_updates'
                  )
    changed_by  = models.ForeignKey(User, on_delete=models.CASCADE)
    from_status = models.CharField(max_length=20)
    to_status   = models.CharField(max_length=20)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'#{self.emergency.pk}: {self.from_status} → {self.to_status}'