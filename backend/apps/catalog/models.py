import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from shared.db.models import TimeStampedModel


class InvalidCourseTransition(Exception):
    """Raised by Course's lifecycle methods on an out-of-order transition —
    views translate this to a 409, never allowing a status change the
    client didn't earn (e.g. publish before approval)."""


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)

    class Meta:
        db_table = "categories"
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        db_table = "tags"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Course(TimeStampedModel):
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    DIFFICULTY_BEGINNER = "beginner"
    DIFFICULTY_INTERMEDIATE = "intermediate"
    DIFFICULTY_ADVANCED = "advanced"
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_BEGINNER, "Beginner"),
        (DIFFICULTY_INTERMEDIATE, "Intermediate"),
        (DIFFICULTY_ADVANCED, "Advanced"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_courses"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    summary = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=10, default="en")
    difficulty = models.CharField(
        max_length=20, choices=DIFFICULTY_CHOICES, default=DIFFICULTY_BEGINNER
    )
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    rejection_reason = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    categories: models.ManyToManyField = models.ManyToManyField(
        Category, through="CourseCategory", related_name="courses", blank=True
    )
    tags: models.ManyToManyField = models.ManyToManyField(
        Tag, through="CourseTag", related_name="courses", blank=True
    )

    class Meta:
        db_table = "courses"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "published_at"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        base = slugify(self.title)[:200] or "course"
        slug = base
        suffix = 1
        while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            suffix += 1
            slug = f"{base}-{suffix}"
        return slug

    # --- Lifecycle: draft -> submitted -> approved/rejected -> published -> archived ---
    # See docs/04-platform-structure/02-core-flows.md §2.

    def submit_for_review(self):
        if self.status not in (self.STATUS_DRAFT, self.STATUS_REJECTED):
            raise InvalidCourseTransition(f"Cannot submit a course from status '{self.status}'")
        self.status = self.STATUS_SUBMITTED
        self.rejection_reason = ""
        self.save(update_fields=["status", "rejection_reason", "updated_at"])

    def approve(self):
        if self.status != self.STATUS_SUBMITTED:
            raise InvalidCourseTransition(f"Cannot approve a course from status '{self.status}'")
        self.status = self.STATUS_APPROVED
        self.save(update_fields=["status", "updated_at"])

    def reject(self, reason: str):
        if self.status != self.STATUS_SUBMITTED:
            raise InvalidCourseTransition(f"Cannot reject a course from status '{self.status}'")
        self.status = self.STATUS_REJECTED
        self.rejection_reason = reason
        self.save(update_fields=["status", "rejection_reason", "updated_at"])

    def publish(self):
        if self.status != self.STATUS_APPROVED:
            raise InvalidCourseTransition(f"Cannot publish a course from status '{self.status}'")
        self.status = self.STATUS_PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])

    def archive(self):
        if self.status != self.STATUS_PUBLISHED:
            raise InvalidCourseTransition(f"Cannot archive a course from status '{self.status}'")
        self.status = self.STATUS_ARCHIVED
        self.save(update_fields=["status", "updated_at"])


class CoursePrerequisite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="prerequisites")
    text = models.CharField(max_length=300)

    class Meta:
        db_table = "course_prerequisites"

    def __str__(self):
        return self.text


class CourseLearningObjective(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="learning_objectives")
    text = models.CharField(max_length=300)

    class Meta:
        db_table = "course_learning_objectives"

    def __str__(self):
        return self.text


class CourseCategory(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        db_table = "course_categories"
        constraints = [
            models.UniqueConstraint(fields=["course", "category"], name="uniq_course_category")
        ]

    def __str__(self):
        return f"{self.course} / {self.category}"


class CourseTag(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        db_table = "course_tags"
        constraints = [models.UniqueConstraint(fields=["course", "tag"], name="uniq_course_tag")]

    def __str__(self):
        return f"{self.course} / {self.tag}"
