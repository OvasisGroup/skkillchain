import uuid

from django.conf import settings
from django.db import models

from apps.catalog.models import Course
from apps.content.models import Lesson


class Enrollment(models.Model):
    SOURCE_DIRECT = "direct"
    SOURCE_PURCHASE = "purchase"
    SOURCE_CHOICES = [(SOURCE_DIRECT, "Direct"), (SOURCE_PURCHASE, "Purchase")]

    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [(STATUS_ACTIVE, "Active"), (STATUS_COMPLETED, "Completed")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="enrollments")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments"
    )
    # "direct" today (no payment gate — Commerce/checkout is M6); a real
    # purchase-driven enrollment in M6 just uses source="purchase" instead
    # of replacing this model.
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_DIRECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "enrollments"
        constraints = [
            models.UniqueConstraint(
                fields=["course", "student"], name="uniq_enrollment_course_student"
            )
        ]
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.student} in {self.course}"


class ProgressTracking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="progress_entries"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_entries")
    percent_complete = models.PositiveSmallIntegerField(default=0)
    last_position_seconds = models.PositiveIntegerField(default=0)
    last_viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "progress_tracking"
        constraints = [
            models.UniqueConstraint(
                fields=["enrollment", "lesson"], name="uniq_progress_enrollment_lesson"
            )
        ]

    def __str__(self):
        return f"{self.enrollment} - {self.lesson} ({self.percent_complete}%)"


class LessonNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="notes")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_notes"
    )
    note_text = models.TextField()
    timestamp_seconds = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "lesson_notes"
        ordering = ["timestamp_seconds"]

    def __str__(self):
        return f"note by {self.student} on {self.lesson}"


class Bookmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="bookmarks")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks"
    )
    timestamp_seconds = models.PositiveIntegerField(default=0)
    label = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bookmarks"
        ordering = ["timestamp_seconds"]

    def __str__(self):
        return f"bookmark by {self.student} on {self.lesson}"


class Wishlist(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="wishlist",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wishlists"

    def __str__(self):
        return f"wishlist for {self.user}"


class WishlistItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="wishlisted_by")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wishlist_items"
        constraints = [
            models.UniqueConstraint(fields=["wishlist", "course"], name="uniq_wishlist_course")
        ]
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.course} in {self.wishlist}"


class RecentlyViewed(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recently_viewed"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="recently_viewed_by")
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recently_viewed"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"], name="uniq_recently_viewed_user_course"
            )
        ]
        ordering = ["-viewed_at"]

    def __str__(self):
        return f"{self.user} viewed {self.course}"


class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.OneToOneField(
        Enrollment, on_delete=models.CASCADE, related_name="certificate"
    )
    certificate_uid = models.CharField(max_length=40, unique=True, editable=False)
    qr_payload = models.CharField(max_length=500)
    # Blank until the PDF-rendering/S3-upload pipeline exists (deferred
    # alongside live_sessions — see M4 commit notes). The certificate is a
    # real, verifiable record either way; only the downloadable file lags.
    pdf_key = models.CharField(max_length=500, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "certificates"

    def __str__(self):
        return f"certificate {self.certificate_uid}"
