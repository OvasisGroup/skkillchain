import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from shared.db.models import TimeStampedModel


class InvalidHackathonTransition(Exception):
    """Raised by Hackathon's lifecycle methods on an out-of-order status
    transition — views translate this to a 409, never allowing a status
    change the client didn't earn (e.g. publish an already-published
    hackathon)."""


def hackathon_cover_upload_path(instance, filename):
    return f"hackathons/{instance.id}/cover/{filename}"


class Hackathon(TimeStampedModel):
    HOST_INTERNAL = "internal"
    HOST_PARTNER = "partner"
    HOST_TYPE_CHOICES = [(HOST_INTERNAL, "Internal"), (HOST_PARTNER, "Partner")]

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CANCELED = "canceled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_CANCELED, "Canceled"),
    ]

    # "Active"/"upcoming"/"completed" (what students browse by) are derived
    # from these timestamps rather than stored — there's no scheduled task
    # to flip a stored value at the right instant, and deriving it is exact
    # and always in sync. `status` only tracks what the organizer actually
    # controls: draft, published, canceled. See `phase` below.
    PHASE_DRAFT = "draft"
    PHASE_UPCOMING = "upcoming"
    PHASE_ACTIVE = "active"
    PHASE_COMPLETED = "completed"
    PHASE_CANCELED = "canceled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="organized_hackathons"
    )
    host_type = models.CharField(max_length=20, choices=HOST_TYPE_CHOICES, default=HOST_INTERNAL)
    # Free-text, not a FK: the platform has no Organization model today (see
    # apps.authorization's "organization" role, which is otherwise unused).
    # A partner-hosted hackathon just names its partner instead of pointing
    # at a first-class record.
    partner_name = models.CharField(max_length=200, blank=True)
    partner_url = models.URLField(max_length=500, blank=True)

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    summary = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to=hackathon_cover_upload_path, blank=True)

    requirements = models.TextField(
        blank=True, help_text="Eligibility, team, and submission requirements."
    )
    prize_summary = models.CharField(
        max_length=300, blank=True, help_text="Short headline, e.g. '$10,000 in prizes'."
    )

    registration_opens_at = models.DateTimeField(null=True, blank=True)
    registration_deadline = models.DateTimeField()
    submission_deadline = models.DateTimeField()
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "hackathons"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "starts_at"]),
            models.Index(fields=["status", "ends_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        base = slugify(self.title)[:200] or "hackathon"
        slug = base
        suffix = 1
        while Hackathon.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            suffix += 1
            slug = f"{base}-{suffix}"
        return slug

    @property
    def phase(self):
        if self.status == self.STATUS_CANCELED:
            return self.PHASE_CANCELED
        if self.status == self.STATUS_DRAFT:
            return self.PHASE_DRAFT
        now = timezone.now()
        if now < self.starts_at:
            return self.PHASE_UPCOMING
        if now <= self.ends_at:
            return self.PHASE_ACTIVE
        return self.PHASE_COMPLETED

    @property
    def is_registration_open(self):
        if self.status != self.STATUS_PUBLISHED:
            return False
        now = timezone.now()
        if self.registration_opens_at and now < self.registration_opens_at:
            return False
        return now <= self.registration_deadline

    # --- Lifecycle: draft -> published -> canceled ---

    def publish(self):
        if self.status != self.STATUS_DRAFT:
            raise InvalidHackathonTransition(f"Cannot publish a hackathon from status '{self.status}'")
        self.status = self.STATUS_PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])

    def cancel(self):
        if self.status == self.STATUS_CANCELED:
            raise InvalidHackathonTransition("Already canceled")
        self.status = self.STATUS_CANCELED
        self.save(update_fields=["status", "updated_at"])


class HackathonRegistration(models.Model):
    STATUS_REGISTERED = "registered"
    STATUS_WITHDRAWN = "withdrawn"
    STATUS_DISQUALIFIED = "disqualified"
    STATUS_CHOICES = [
        (STATUS_REGISTERED, "Registered"),
        (STATUS_WITHDRAWN, "Withdrawn"),
        (STATUS_DISQUALIFIED, "Disqualified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE, related_name="registrations")
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hackathon_registrations"
    )
    # The hackathon "registration form": free-form team/participation detail
    # collected at registration time. Kept as plain fields rather than a
    # generic form-builder — no requirement anywhere calls for organizer-
    # defined custom fields.
    team_name = models.CharField(max_length=150, blank=True)
    motivation = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REGISTERED)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hackathon_registrations"
        constraints = [
            models.UniqueConstraint(
                fields=["hackathon", "participant"], name="uniq_registration_hackathon_participant"
            )
        ]
        ordering = ["-registered_at"]

    def __str__(self):
        return f"{self.participant} registered for {self.hackathon}"


class HackathonSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration = models.OneToOneField(
        HackathonRegistration, on_delete=models.CASCADE, related_name="submission"
    )
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    repo_url = models.URLField(max_length=500, blank=True)
    demo_url = models.URLField(max_length=500, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hackathon_submissions"
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.title} ({self.registration.participant})"


class HackathonWinner(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE, related_name="winners")
    submission = models.ForeignKey(
        HackathonSubmission, on_delete=models.PROTECT, related_name="winner_entries"
    )
    placement = models.PositiveSmallIntegerField(help_text="1 = first place, 2 = second, etc.")
    prize_description = models.CharField(max_length=300, blank=True)
    announced_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hackathon_winners"
        constraints = [
            models.UniqueConstraint(
                fields=["hackathon", "placement"], name="uniq_winner_hackathon_placement"
            ),
            models.UniqueConstraint(
                fields=["hackathon", "submission"], name="uniq_winner_hackathon_submission"
            ),
        ]
        ordering = ["placement"]

    def __str__(self):
        return f"#{self.placement} {self.submission} — {self.hackathon}"
