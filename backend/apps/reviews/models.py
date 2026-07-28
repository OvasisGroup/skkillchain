import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.catalog.models import Course


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review_text = models.TextField(blank=True, default="")
    # Set once at creation from the completed-enrollment check in
    # services.create_review — a later refund/enrollment change doesn't
    # retroactively flip this, same "point-in-time fact" treatment as
    # AffiliateCommission.payout_status elsewhere in this codebase.
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reviews"
        constraints = [
            models.UniqueConstraint(fields=["course", "user"], name="uniq_review_course_user")
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} rated {self.course_id}: {self.rating}"


class CourseDiscussionPost(models.Model):
    # Not in the ERD's documented physical schema (only `reviews` is listed
    # there under Courses), but both the API doc (§10 — GET/POST
    # /courses/{course_id}/discussions) and the WebSocket channel list
    # (§15 — ws/course/{course_id}/discussion) require course discussion
    # posts as their own resource. Modeled as a flat post rather than
    # reusing messaging's Thread+Message: there's no separate "start a
    # discussion thread" step in the API doc, just posting directly under
    # a course.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="discussion_posts")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_discussion_posts",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "course_discussion_posts"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user} on {self.course_id}: {self.body[:30]}"
