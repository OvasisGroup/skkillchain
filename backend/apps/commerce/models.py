import uuid

from django.conf import settings
from django.db import models

from apps.catalog.models import Course
from shared.db.models import TimeStampedModel


class PaymentMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_methods"
    )
    provider = models.CharField(max_length=20)
    provider_pm_id = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "payment_methods"

    def __str__(self):
        return f"{self.provider} method for {self.user}"


class Promotion(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_ENDED = "ended"
    STATUS_CHOICES = [(STATUS_DRAFT, "Draft"), (STATUS_ACTIVE, "Active"), (STATUS_ENDED, "Ended")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    campaign_type = models.CharField(max_length=50, blank=True)
    banner_asset_key = models.CharField(max_length=500, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_promotions"
    )

    class Meta:
        db_table = "promotions"

    def __str__(self):
        return self.name


class Coupon(models.Model):
    DISCOUNT_PERCENT = "percent"
    DISCOUNT_FIXED = "fixed"
    DISCOUNT_TYPE_CHOICES = [(DISCOUNT_PERCENT, "Percent"), (DISCOUNT_FIXED, "Fixed amount")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    per_user_limit = models.PositiveIntegerField(null=True, blank=True)
    promotion = models.ForeignKey(
        Promotion, on_delete=models.SET_NULL, null=True, blank=True, related_name="coupons"
    )
    # Not in the documented schema's coupons table, but required by the
    # documented instructor endpoint POST
    # /instructor/courses/{courseId}/coupons — without a course scope, a
    # "course-scoped coupon" has nothing to scope to. Left null for
    # platform-wide (admin-created) coupons.
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, null=True, blank=True, related_name="coupons"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_coupons"
    )

    class Meta:
        db_table = "coupons"

    def __str__(self):
        return self.code


class GiftCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    expires_at = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_gift_cards",
    )

    class Meta:
        db_table = "gift_cards"

    def __str__(self):
        return self.code

    @property
    def is_expired(self):
        from django.utils import timezone

        return self.expires_at is not None and self.expires_at < timezone.now()


class Order(TimeStampedModel):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CANCELED = "canceled"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_CANCELED, "Canceled"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gift_card_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    # Applied-but-not-yet-finalized coupon/gift-card intent — the actual
    # CouponRedemption / GiftCardRedemption rows (and the gift card balance
    # deduction) are only created once payment succeeds, so an abandoned
    # cart never permanently reserves/burns a gift card balance. See
    # apps/commerce/services.py finalize_order_payment().
    applied_coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    applied_gift_card = models.ForeignKey(
        GiftCard, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.id} ({self.status})"


class OrderItem(models.Model):
    ITEM_TYPE_COURSE = "course"
    ITEM_TYPE_PLAN = "plan"
    ITEM_TYPE_CHOICES = [(ITEM_TYPE_COURSE, "Course"), (ITEM_TYPE_PLAN, "Plan")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default=ITEM_TYPE_COURSE)
    item_id = models.UUIDField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "order_items"

    def __str__(self):
        return f"{self.item_type}:{self.item_id} x{self.quantity}"


class CouponRedemption(models.Model):
    """
    Not in the documented schema — added because usage_limit/per_user_limit
    on Coupon are unenforceable without a redemption log. Written only at
    payment-success time (see finalize_order_payment), same reasoning as
    GiftCardRedemption below.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="redemptions")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coupon_redemptions"
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="coupon_redemption")
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "coupon_redemptions"

    def __str__(self):
        return f"{self.user} redeemed {self.coupon}"


class GiftCardRedemption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gift_card = models.ForeignKey(GiftCard, on_delete=models.CASCADE, related_name="redemptions")
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="gift_card_redemption"
    )
    amount_applied = models.DecimalField(max_digits=10, decimal_places=2)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gift_card_redemptions"

    def __str__(self):
        return f"{self.amount_applied} of {self.gift_card} on {self.order_id}"


class Payment(TimeStampedModel):
    STATUS_PENDING = "pending"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    provider = models.CharField(max_length=20)
    provider_payment_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.provider} payment for {self.order_id} ({self.status})"


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="invoice")
    invoice_number = models.CharField(max_length=50, unique=True)
    tax_metadata = models.JSONField(default=dict, blank=True)
    # No PDF rendering pipeline exists yet — same deferred scope as
    # Certificate.pdf_key in apps.learning (M4 notes). Blank until a
    # rendering/storage integration is built.
    pdf_key = models.CharField(max_length=500, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoices"

    def __str__(self):
        return self.invoice_number


class Refund(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    provider_refund_id = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "refunds"

    def __str__(self):
        return f"Refund for {self.payment_id} ({self.status})"


class WebhookEvent(models.Model):
    """
    Not in the documented schema — required by the M6 security checklist's
    "idempotent under redelivery (dedupe on provider event ID)". The
    unique constraint is the actual dedupe mechanism: a second delivery of
    the same provider+event_id hits IntegrityError, which the view catches
    and treats as an already-processed no-op rather than reprocessing.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=20)
    provider_event_id = models.CharField(max_length=255)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "webhook_events"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_event_id"], name="uniq_webhook_event_per_provider"
            )
        ]

    def __str__(self):
        return f"{self.provider}:{self.provider_event_id}"
