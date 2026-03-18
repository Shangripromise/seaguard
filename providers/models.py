from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


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

    def average_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return None
        return round(sum(r.score for r in ratings) / len(ratings), 1)

    def rating_count(self):
        return self.ratings.count()

    def __str__(self):
        return f'{self.company_name} ({self.verification_status})'


class ProviderRating(models.Model):
    provider   = models.ForeignKey(RecoveryProvider, on_delete=models.CASCADE, related_name='ratings')
    rated_by   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    score      = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('provider', 'rated_by')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.provider.company_name} — {self.score}/5 by {self.rated_by.username}'