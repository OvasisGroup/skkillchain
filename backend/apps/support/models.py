import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class SupportTicket(models.Model):
    CATEGORY_BILLING = "billing"
    CATEGORY_TECHNICAL = "technical"
    CATEGORY_COURSE_CONTENT = "course_content"
    CATEGORY_OTHER = "other"
    CATEGORY_CHOICES = [
        (CATEGORY_BILLING, "Billing"),
        (CATEGORY_TECHNICAL, "Technical"),
        (CATEGORY_COURSE_CONTENT, "Course Content"),
        (CATEGORY_OTHER, "Other"),
    ]

    PRIORITY_LOW = "low"
    PRIORITY_NORMAL = "normal"
    PRIORITY_HIGH = "high"
    PRIORITY_URGENT = "urgent"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_NORMAL, "Normal"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_URGENT, "Urgent"),
    ]

    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_RESOLVED = "resolved"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_CLOSED, "Closed"),
    ]

    # No SLA policy is documented anywhere in the SRS/product docs — same
    # "no documented source of truth" gap as PLATFORM_COMMISSION_RATE in
    # config/settings/base.py. These are reasonable defaults pending a real
    # support policy, used only by is_sla_breached below.
    SLA_TARGET_RESPONSE = {
        PRIORITY_URGENT: timedelta(hours=4),
        PRIORITY_HIGH: timedelta(hours=8),
        PRIORITY_NORMAL: timedelta(hours=24),
        PRIORITY_LOW: timedelta(hours=72),
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_tickets"
    )
    # Set by an admin assignment workflow — not built in this milestone
    # (M9's own `support` app entry owns GET/PATCH /admin/support-tickets
    # per docs/07-delivery-planning/02-backend-build-milestones.md), so
    # this stays null for every ticket created here.
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_support_tickets",
    )
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "support_tickets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.status})"

    @property
    def is_sla_breached(self) -> bool:
        if self.status in (self.STATUS_RESOLVED, self.STATUS_CLOSED):
            return False
        target = self.SLA_TARGET_RESPONSE.get(self.priority, timedelta(hours=24))
        return timezone.now() - self.created_at > target


class SupportTicketMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_ticket_messages"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "support_ticket_messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender} on {self.ticket_id}"
