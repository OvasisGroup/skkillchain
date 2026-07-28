import uuid

from django.conf import settings
from django.db import models

from apps.catalog.models import Course
from shared.db.models import TimeStampedModel


class ConferencingAccount(TimeStampedModel):
    PROVIDER_ZOOM = "zoom"
    PROVIDER_GOOGLE_MEET = "google_meet"
    PROVIDER_CHOICES = [(PROVIDER_ZOOM, "Zoom"), (PROVIDER_GOOGLE_MEET, "Google Meet")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conferencing_accounts"
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    external_account_id = models.CharField(max_length=255, blank=True)
    # Encrypted via shared.crypto — never serialized to the API, never
    # logged. See apps/live_sessions/conferencing/ for where these are
    # read/written.
    access_token_encrypted = models.TextField()
    refresh_token_encrypted = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "conferencing_accounts"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "provider"],
                condition=models.Q(revoked_at__isnull=True),
                name="uniq_active_conferencing_account_per_provider",
            )
        ]

    def __str__(self):
        return f"{self.provider} account for {self.user}"

    @property
    def is_active(self):
        return self.revoked_at is None


class LiveSession(TimeStampedModel):
    STATUS_SCHEDULED = "scheduled"
    STATUS_LIVE = "live"
    STATUS_ENDED = "ended"
    STATUS_CANCELED = "canceled"
    STATUS_CHOICES = [
        (STATUS_SCHEDULED, "Scheduled"),
        (STATUS_LIVE, "Live"),
        (STATUS_ENDED, "Ended"),
        (STATUS_CANCELED, "Canceled"),
    ]

    # Join links are handed out from this many minutes before
    # scheduled_start_at through scheduled_end_at — see
    # apps/live_sessions/views.LiveSessionJoinView and
    # docs/04-platform-structure/02-core-flows.md §9.
    JOIN_WINDOW_MINUTES_BEFORE_START = 15

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="live_sessions", null=True, blank=True
    )
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="hosted_live_sessions"
    )
    conferencing_account = models.ForeignKey(
        ConferencingAccount, on_delete=models.PROTECT, related_name="live_sessions"
    )
    provider = models.CharField(max_length=20, choices=ConferencingAccount.PROVIDER_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    scheduled_start_at = models.DateTimeField()
    scheduled_end_at = models.DateTimeField()
    timezone = models.CharField(max_length=50, default="UTC")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    external_meeting_id = models.CharField(max_length=255, blank=True)
    join_url = models.URLField(max_length=1000, blank=True)
    host_join_url = models.URLField(max_length=1000, blank=True)
    is_recorded = models.BooleanField(default=True)

    class Meta:
        db_table = "live_sessions"
        ordering = ["scheduled_start_at"]
        indexes = [models.Index(fields=["course", "scheduled_start_at"])]

    def __str__(self):
        return f"{self.title} ({self.scheduled_start_at:%Y-%m-%d %H:%M})"


class LiveSessionRegistration(models.Model):
    STATUS_REGISTERED = "registered"
    STATUS_ATTENDED = "attended"
    STATUS_NO_SHOW = "no_show"
    STATUS_CANCELED = "canceled"
    STATUS_CHOICES = [
        (STATUS_REGISTERED, "Registered"),
        (STATUS_ATTENDED, "Attended"),
        (STATUS_NO_SHOW, "No-show"),
        (STATUS_CANCELED, "Canceled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    live_session = models.ForeignKey(
        LiveSession, on_delete=models.CASCADE, related_name="registrations"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="live_session_registrations",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REGISTERED)
    registered_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    attended_duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "live_session_registrations"
        constraints = [
            models.UniqueConstraint(
                fields=["live_session", "student"], name="uniq_registration_session_student"
            )
        ]

    def __str__(self):
        return f"{self.student} registered for {self.live_session}"


class LiveSessionRecording(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    live_session = models.OneToOneField(
        LiveSession, on_delete=models.CASCADE, related_name="recording"
    )
    provider_recording_id = models.CharField(max_length=255, blank=True)
    playback_url = models.URLField(max_length=1000, blank=True)
    download_key = models.CharField(max_length=500, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    available_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "live_session_recordings"

    def __str__(self):
        return f"recording for {self.live_session}"
