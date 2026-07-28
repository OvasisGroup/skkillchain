import uuid

from django.conf import settings
from django.db import models

CHANNEL_IN_APP = "in_app"
CHANNEL_EMAIL = "email"
CHANNEL_SMS = "sms"
CHANNEL_PUSH = "push"
CHANNEL_CHOICES = [
    (CHANNEL_IN_APP, "In-app"),
    (CHANNEL_EMAIL, "Email"),
    (CHANNEL_SMS, "SMS"),
    (CHANNEL_PUSH, "Push"),
]


class NotificationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    locale = models.CharField(max_length=10, default="en")
    subject_template = models.CharField(max_length=255, blank=True, default="")
    # str.format()-style placeholders (e.g. "{sender_name}") filled in from
    # the context dict passed to notifications.services.notify() at
    # dispatch time — editing this row changes the next send with no
    # deploy, which is the whole point of templating this instead of
    # hardcoding copy into each call site.
    body_template = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "notification_templates"
        constraints = [
            models.UniqueConstraint(
                fields=["code", "locale"], name="uniq_notification_template_code_locale"
            )
        ]

    def __str__(self):
        return f"{self.code} ({self.channel}/{self.locale})"


class EmailTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100)
    locale = models.CharField(max_length=10, default="en")
    subject = models.CharField(max_length=255)
    html_body = models.TextField(blank=True, default="")
    text_body = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "email_templates"
        constraints = [
            models.UniqueConstraint(
                fields=["code", "locale"], name="uniq_email_template_code_locale"
            )
        ]

    def __str__(self):
        return f"{self.code} ({self.locale})"


class Notification(models.Model):
    TYPE_MESSAGE = "message"
    TYPE_SUPPORT_TICKET = "support_ticket"
    TYPE_LIVE_SESSION_REMINDER = "live_session_reminder"
    TYPE_SYSTEM = "system"
    TYPE_CHOICES = [
        (TYPE_MESSAGE, "Message"),
        (TYPE_SUPPORT_TICKET, "Support Ticket"),
        (TYPE_LIVE_SESSION_REMINDER, "Live Session Reminder"),
        (TYPE_SYSTEM, "System"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    # A lookup key into NotificationTemplate, not a real Django ForeignKey:
    # the ERD documents this as template_code -> notification_templates.code
    # (ON DELETE SET NULL), but code is only unique together with locale, so
    # it can't be an enforceable FK target on its own. Kept as a plain
    # indexed string; rendering resolves it against (code, channel) at
    # dispatch time in tasks.py.
    template_code = models.CharField(max_length=100, blank=True, default="", db_index=True)
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    title = models.CharField(max_length=255, blank=True, default="")
    body = models.TextField(blank=True, default="")
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type}/{self.channel} -> {self.user_id}"
