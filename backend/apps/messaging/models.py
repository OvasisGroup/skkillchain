import uuid

from django.conf import settings
from django.db import models


class Thread(models.Model):
    TYPE_DIRECT = "direct"
    TYPE_GROUP = "group"
    THREAD_TYPE_CHOICES = [(TYPE_DIRECT, "Direct"), (TYPE_GROUP, "Group")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread_type = models.CharField(max_length=20, choices=THREAD_TYPE_CHOICES, default=TYPE_DIRECT)
    subject = models.CharField(max_length=255, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_threads"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "threads"
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject or f"Thread {self.id}"


class ThreadParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="thread_participations"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "thread_participants"
        constraints = [
            models.UniqueConstraint(fields=["thread", "user"], name="uniq_thread_participant")
        ]

    def __str__(self):
        return f"{self.user} in {self.thread_id}"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    body = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender} in {self.thread_id}: {self.body[:30]}"
