import uuid

from django.conf import settings
from django.db import models

from apps.catalog.models import Course
from apps.content.models import Lesson


class AnalyticsEvent(models.Model):
    """
    Append-only event stream. The schema doc calls for this table to be
    monthly-partitioned (same as audit_logs), but audit_logs — under the
    identical documented requirement — isn't actually partitioned
    anywhere in this codebase either (no RunSQL/partition migration
    exists for it). Treated the same documented, consistent way here:
    partitioning deferred, not silently dropped.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_name = models.CharField(max_length=100)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="analytics_events",
    )
    course = models.ForeignKey(
        Course, null=True, blank=True, on_delete=models.SET_NULL, related_name="analytics_events"
    )
    session_id = models.CharField(max_length=100, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_events"
        ordering = ["-occurred_at"]
        indexes = [models.Index(fields=["event_name", "occurred_at"])]

    def __str__(self):
        return f"{self.event_name} @ {self.occurred_at}"


class RevenueDailyAggregate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period_start = models.DateField()
    period_end = models.DateField()
    currency = models.CharField(max_length=3)
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "revenue_daily_aggregates"
        ordering = ["-period_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["period_start", "period_end", "currency"],
                name="uniq_revenue_period_currency",
            )
        ]

    def __str__(self):
        return f"revenue {self.period_start}..{self.period_end} ({self.currency})"


class EngagementDailyAggregate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="engagement_aggregates")
    period_start = models.DateField()
    period_end = models.DateField()
    active_students_count = models.PositiveIntegerField(default=0)
    new_enrollments_count = models.PositiveIntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "engagement_daily_aggregates"
        ordering = ["-period_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "period_start", "period_end"],
                name="uniq_engagement_course_period",
            )
        ]

    def __str__(self):
        return f"engagement {self.course_id} {self.period_start}..{self.period_end}"


class CourseCompletionAggregate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="completion_aggregates")
    period_start = models.DateField()
    period_end = models.DateField()
    enrollments_count = models.PositiveIntegerField(default=0)
    completions_count = models.PositiveIntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percent
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "course_completion_aggregates"
        ordering = ["-period_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "period_start", "period_end"],
                name="uniq_completion_course_period",
            )
        ]

    def __str__(self):
        return f"completion {self.course_id} {self.period_start}..{self.period_end}"


class LessonWatchTimeAggregate(models.Model):
    # last_position_seconds (apps.learning.ProgressTracking) is the only
    # existing watch-time proxy anywhere in this codebase — there's no
    # dedicated watch-time/duration-watched field, so this is a
    # best-effort figure (the furthest position a student reached), not a
    # true accumulated-seconds-watched metric.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="watch_time_aggregates")
    period_start = models.DateField()
    period_end = models.DateField()
    total_watch_seconds = models.PositiveBigIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lesson_watch_time_aggregates"
        ordering = ["-period_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["lesson", "period_start", "period_end"],
                name="uniq_watchtime_lesson_period",
            )
        ]

    def __str__(self):
        return f"watch-time {self.lesson_id} {self.period_start}..{self.period_end}"


class LessonDropOffAggregate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="drop_off_aggregates")
    period_start = models.DateField()
    period_end = models.DateField()
    started_count = models.PositiveIntegerField(default=0)
    completed_count = models.PositiveIntegerField(default=0)
    drop_off_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percent
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lesson_drop_off_aggregates"
        ordering = ["-period_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["lesson", "period_start", "period_end"], name="uniq_dropoff_lesson_period"
            )
        ]

    def __str__(self):
        return f"drop-off {self.lesson_id} {self.period_start}..{self.period_end}"


class InstructorEarningsAggregate(models.Model):
    # Sourced from apps.payouts' own Transaction ledger (owner_type=
    # instructor), not re-derived from raw Order data — the payouts app's
    # own reconciliation comment already recommends this as the source of
    # truth for anything summarizing instructor earnings.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="earnings_aggregates"
    )
    period_start = models.DateField()
    period_end = models.DateField()
    currency = models.CharField(max_length=3, default="USD")
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "instructor_earnings_aggregates"
        ordering = ["-period_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["instructor", "period_start", "period_end", "currency"],
                name="uniq_earnings_instructor_period",
            )
        ]

    def __str__(self):
        return f"earnings {self.instructor_id} {self.period_start}..{self.period_end}"
