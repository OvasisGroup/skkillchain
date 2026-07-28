import secrets
import uuid

from django.conf import settings
from django.db import models

from apps.commerce.models import Order


def _generate_referral_code() -> str:
    return secrets.token_hex(4).upper()  # 8 hex chars, e.g. "A1B2C3D4"


class AffiliateAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="affiliate_account"
    )
    referral_code = models.CharField(max_length=20, unique=True, default=_generate_referral_code)
    # Percent, e.g. 10.00 means 10% of the referred order's total_amount.
    # No documented source of truth for the default rate exists (same gap
    # as PLATFORM_COMMISSION_RATE) — settings.AFFILIATE_DEFAULT_COMMISSION_RATE.
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = "affiliate_accounts"

    def __str__(self):
        return f"{self.user} ({self.referral_code})"


class AffiliateReferral(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONVERTED = "converted"
    STATUS_CHOICES = [(STATUS_PENDING, "Pending"), (STATUS_CONVERTED, "Converted")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    affiliate = models.ForeignKey(
        AffiliateAccount, on_delete=models.CASCADE, related_name="referrals"
    )
    referred_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referred_by"
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="affiliate_referral")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "affiliate_referrals"

    def __str__(self):
        return f"{self.affiliate} referred {self.referred_user} ({self.status})"


class AffiliateCommission(models.Model):
    PAYOUT_STATUS_PENDING = "pending"
    PAYOUT_STATUS_PAID = "paid"
    PAYOUT_STATUS_CHOICES = [(PAYOUT_STATUS_PENDING, "Pending"), (PAYOUT_STATUS_PAID, "Paid")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referral = models.OneToOneField(
        AffiliateReferral, on_delete=models.CASCADE, related_name="commission"
    )
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Mirrors whether the underlying wallet credit has been swept into a
    # Payout yet — set to "paid" when apps.payouts.services.request_payout
    # sweeps the corresponding Transaction, not tracked independently.
    payout_status = models.CharField(
        max_length=20, choices=PAYOUT_STATUS_CHOICES, default=PAYOUT_STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "affiliate_commissions"

    def __str__(self):
        return f"{self.commission_amount} for {self.referral_id}"
