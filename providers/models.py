from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class RecoveryProvider(models.Model):

    VERIFICATION_CHOICES = [
        ('pending',  'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # CR2 — service type used in equipment compatibility scoring
    SERVICE_TYPE_CHOICES = [
        ('towing',    'Towing'),
        ('salvage',   'Salvage'),
        ('medical',   'Medical'),
        ('fire',      'Fire Fighting'),
        ('fuel',      'Fuel Delivery'),
        ('general',   'General Recovery'),
    ]

    user                  = models.OneToOneField(User, on_delete=models.CASCADE,
                                                 related_name='provider_profile')
    company_name          = models.CharField(max_length=200)
    contact_person        = models.CharField(max_length=100)
    phone_number          = models.CharField(max_length=20)
    business_registration = models.CharField(max_length=50)
    service_area          = models.CharField(max_length=200)
    # CR2 — service type for equipment compatibility scoring
    service_type          = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES,
                                             default='general')
    # CR2 — average response time in minutes, updated on each job completion
    avg_response_minutes  = models.PositiveIntegerField(default=60)
    # CR2 / CR1 — availability flag for real-time filtering and ranking
    is_available          = models.BooleanField(default=True)
    verification_status   = models.CharField(max_length=20, choices=VERIFICATION_CHOICES,
                                             default='pending')
    created_at            = models.DateTimeField(auto_now_add=True)

    def average_rating(self):
        """Returns approved ratings average, used in CR2 ranking score."""
        ratings = self.ratings.filter(moderation_status='approved')
        if not ratings:
            return None
        return round(sum(r.score for r in ratings) / len(ratings), 1)

    def rating_count(self):
        return self.ratings.filter(moderation_status='approved').count()

    def ranking_score(self, incident_lat=None, incident_lon=None,
                      incident_type=None):
        """
        CR2 — Weighted composite score used for intelligent dispatch.
        Weights per SRS FR-RP-DISP-001:
          Proximity               35%  (lower distance = higher score)
          Average provider rating 25%
          Historical response time 20% (lower time = higher score)
          Equipment compatibility  15%
          Fleet availability        5%

        Proximity and equipment scoring are simplified here because we have
        no real GPS routing in the MVP — distance is approximated from
        service_area text match, equipment from service_type match.
        Full implementation would use PostGIS in production (v1.1).
        """
        score = 0.0

        # --- 35% Proximity ---
        # MVP: award full proximity points if provider is approved and available.
        # Production would calculate haversine distance from incident coords.
        proximity_score = 80 if self.is_available else 40
        score += proximity_score * 0.35

        # --- 25% Average rating ---
        avg = self.average_rating()
        if avg is not None:
            # Scale 1-5 stars to 0-100
            rating_score = (avg / 5.0) * 100
        else:
            # No ratings yet — neutral score
            rating_score = 50
        score += rating_score * 0.25

        # --- 20% Response time ---
        # Lower response time = higher score.
        # Cap at 120 minutes; anything above scores 0.
        capped_time = min(self.avg_response_minutes, 120)
        response_score = ((120 - capped_time) / 120) * 100
        score += response_score * 0.20

        # --- 15% Equipment / service type compatibility ---
        # Full match = 100, partial = 50, no match = 0
        COMPATIBILITY = {
            'fire':          ['fire', 'general'],
            'flooding':      ['salvage', 'general', 'towing'],
            'medical':       ['medical', 'general'],
            'collision':     ['towing', 'salvage', 'general'],
            'grounding':     ['towing', 'salvage', 'general'],
            'man_overboard': ['medical', 'general'],
            'other':         ['general'],
        }
        compatible_types = COMPATIBILITY.get(incident_type, ['general'])
        if self.service_type == compatible_types[0]:
            equipment_score = 100
        elif self.service_type in compatible_types:
            equipment_score = 50
        else:
            equipment_score = 0
        score += equipment_score * 0.15

        # --- 5% Fleet availability ---
        availability_score = 100 if self.is_available else 0
        score += availability_score * 0.05

        return round(score, 2)

    def __str__(self):
        return f'{self.company_name} ({self.verification_status})'


class ProviderRating(models.Model):

    # CR4 — moderation states per FR-SA-MOD-001/002/003
    MODERATION_CHOICES = [
        ('pending',  'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    REJECTION_REASONS = [
        ('inappropriate', 'Inappropriate Content'),
        ('fraud',         'Suspected Fraud'),
        ('duplicate',     'Duplicate Submission'),
        ('off_topic',     'Off-Topic'),
        ('other',         'Other'),
    ]

    provider          = models.ForeignKey(RecoveryProvider, on_delete=models.CASCADE,
                                          related_name='ratings')
    rated_by          = models.ForeignKey(User, on_delete=models.CASCADE,
                                          related_name='ratings_given')
    score             = models.IntegerField(validators=[MinValueValidator(1),
                                                        MaxValueValidator(5)])
    comment           = models.TextField(blank=True)
    # CR4 moderation fields
    moderation_status = models.CharField(max_length=20, choices=MODERATION_CHOICES,
                                         default='pending')
    rejection_reason  = models.CharField(max_length=20, choices=REJECTION_REASONS,
                                         blank=True)
    moderated_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                          null=True, blank=True,
                                          related_name='moderated_ratings')
    moderated_at      = models.DateTimeField(null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('provider', 'rated_by')
        ordering        = ['-created_at']

    def __str__(self):
        return f'{self.provider.company_name} — {self.score}/5 by {self.rated_by.username}'