from django.db import models
from django.conf import settings


# ── CR6: Voucher Service ──────────────────────────────────────────────────────

class Voucher(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed',      'Fixed Amount'),
    ]
    APPLIES_TO_CHOICES = [
        ('membership', 'Membership Fee'),
        ('callout',    'Emergency Call-Out'),
        ('general',    'General / Any Service'),
    ]

    code           = models.CharField(max_length=20, unique=True, db_index=True)
    description    = models.CharField(max_length=200, blank=True)
    discount_type  = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES,
                                      default='percentage')
    discount_value = models.DecimalField(max_digits=6, decimal_places=2,
                                         help_text='Percentage (0-100) or fixed £ amount')
    applies_to     = models.CharField(max_length=20, choices=APPLIES_TO_CHOICES,
                                      default='general')
    expiry_date    = models.DateField(null=True, blank=True)
    max_uses       = models.PositiveIntegerField(null=True, blank=True,
                                                 help_text='Leave blank for unlimited uses')
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    created_by     = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='vouchers_created'
    )

    def times_used(self):
        return self.redemptions.count()

    def is_valid(self):
        from django.utils import timezone
        if not self.is_active:
            return False, 'This voucher is no longer active.'
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return False, 'This voucher has expired.'
        if self.max_uses is not None and self.times_used() >= self.max_uses:
            return False, 'This voucher has reached its maximum number of uses.'
        return True, None

    def __str__(self):
        return f'{self.code} ({self.get_discount_type_display()} — {self.discount_value})'

    class Meta:
        ordering = ['-created_at']


class VoucherRedemption(models.Model):
    voucher     = models.ForeignKey(Voucher, on_delete=models.CASCADE,
                                    related_name='redemptions')
    redeemed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='voucher_redemptions'
    )
    redeemed_at = models.DateTimeField(auto_now_add=True)
    applied_to  = models.CharField(max_length=20,
                                   choices=Voucher.APPLIES_TO_CHOICES, default='general')
    notes       = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return (f'{self.redeemed_by.username} used {self.voucher.code} '
                f'at {self.redeemed_at:%Y-%m-%d %H:%M}')

    class Meta:
        ordering = ['-redeemed_at']
        unique_together = [('voucher', 'redeemed_by')]