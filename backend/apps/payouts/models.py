import uuid

from django.conf import settings
from django.db import models


class Wallet(models.Model):
    # Scoped to "instructor" only for now — the documented schema's
    # owner_type is generic (an org or an affiliate could plausibly have
    # a wallet too), but only instructor course-revenue share is wired up
    # in this slice. Affiliate commissions are a deferred follow-up (see
    # the M6 milestone doc) and will reuse this same model when built.
    OWNER_INSTRUCTOR = "instructor"
    OWNER_TYPE_CHOICES = [(OWNER_INSTRUCTOR, "Instructor")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_type = models.CharField(
        max_length=20, choices=OWNER_TYPE_CHOICES, default=OWNER_INSTRUCTOR
    )
    owner_id = models.UUIDField()
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")

    class Meta:
        db_table = "wallets"
        constraints = [
            models.UniqueConstraint(
                fields=["owner_type", "owner_id", "currency"], name="uniq_wallet_per_owner_currency"
            )
        ]

    def __str__(self):
        return f"{self.owner_type}:{self.owner_id} wallet ({self.balance_amount} {self.currency})"


class Transaction(models.Model):
    DIRECTION_CREDIT = "credit"
    DIRECTION_DEBIT = "debit"
    DIRECTION_CHOICES = [(DIRECTION_CREDIT, "Credit"), (DIRECTION_DEBIT, "Debit")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="transactions")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=100)
    # Generic pointer to whatever produced this transaction (e.g.
    # "Payment"/<payment_id> for a course-sale credit, "Payout"/<payout_id>
    # for a payout debit) — same lightweight polymorphic-reference pattern
    # as apps.commerce.OrderItem, not a real FK.
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.UUIDField(null=True, blank=True)
    # Set once this credit has been swept into a Payout — lets a
    # reconciliation query independently re-derive a payout's total from
    # exactly the transactions it covered, without trusting the payout
    # job's own stored amount_gross.
    payout = models.ForeignKey(
        "Payout", on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transactions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.direction} {self.amount} on {self.wallet_id} ({self.reason})"


class Payout(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payouts"
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    amount_gross = models.DecimalField(max_digits=12, decimal_places=2)
    # No deductions (processing fees, withholding) are modeled yet, so
    # amount_net always equals amount_gross today — kept as its own
    # column (matching the documented schema) so a real deduction can be
    # introduced later without a schema change.
    amount_net = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payouts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payout {self.amount_net} to {self.instructor_id} ({self.status})"
