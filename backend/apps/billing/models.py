import uuid
from datetime import timedelta

from django.db import models


class Plan(models.Model):
    INTERVAL_MONTHLY = "monthly"
    INTERVAL_YEARLY = "yearly"
    INTERVAL_CHOICES = [(INTERVAL_MONTHLY, "Monthly"), (INTERVAL_YEARLY, "Yearly")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    billing_interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    # "seat_model" per the documented schema — not enforced anywhere yet
    # (no org-seat purchasing flow exists), stored for the frontend to
    # read. See subscriber_type below for the related organization gap.
    seat_model = models.CharField(max_length=50, blank=True)
    features_json = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "plans"

    def __str__(self):
        return self.name

    @property
    def interval_timedelta(self) -> timedelta:
        return timedelta(days=365 if self.billing_interval == self.INTERVAL_YEARLY else 30)


class Subscription(models.Model):
    # The documented schema's subscriber_type/subscriber_id is polymorphic
    # (user or organization), but no Organization model exists yet in this
    # codebase (a later milestone) — subscriber_type is scoped to "user"
    # only for now. Adding "organization" later is additive: the column
    # and the choice already exist in shape, just not exercised.
    SUBSCRIBER_USER = "user"
    SUBSCRIBER_TYPE_CHOICES = [(SUBSCRIBER_USER, "User")]

    STATUS_ACTIVE = "active"
    STATUS_CANCELED = "canceled"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_CANCELED, "Canceled"),
        (STATUS_EXPIRED, "Expired"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscriber_type = models.CharField(
        max_length=20, choices=SUBSCRIBER_TYPE_CHOICES, default=SUBSCRIBER_USER
    )
    subscriber_id = models.UUIDField()
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    started_at = models.DateTimeField(auto_now_add=True)
    renews_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "subscriptions"
        constraints = [
            models.UniqueConstraint(
                fields=["subscriber_type", "subscriber_id", "plan"],
                condition=models.Q(status="active"),
                name="uniq_active_subscription_per_subscriber_plan",
            )
        ]

    def __str__(self):
        return f"{self.subscriber_type}:{self.subscriber_id} on {self.plan}"

    @property
    def user_id(self):
        """Convenience accessor for the common case — subscriber_id *is*
        the user id while subscriber_type is scoped to "user" only."""
        return self.subscriber_id if self.subscriber_type == self.SUBSCRIBER_USER else None
