import uuid

from django.conf import settings
from django.db import models


class LegalHold(models.Model):
    """
    An open legal/financial matter (dispute, investigation, court order)
    that blocks erasure of a user's PII until released. Independent of any
    particular DataErasureRequest — a hold can be placed before a request
    ever exists, and released long after one was blocked by it.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="legal_holds"
    )
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "legal_holds"
        ordering = ["-created_at"]

    def __str__(self):
        status = "active" if self.released_at is None else "released"
        return f"LegalHold({self.user_id}, {status})"

    @property
    def is_active(self):
        return self.released_at is None


class DataErasureRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_BLOCKED = "blocked"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_BLOCKED, "Blocked"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="erasure_requests"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    block_reason = models.TextField(blank=True, default="")
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "data_erasure_requests"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"DataErasureRequest({self.user_id}, {self.status})"
