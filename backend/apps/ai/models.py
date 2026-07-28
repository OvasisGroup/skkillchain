import uuid

from django.conf import settings
from django.db import models

from apps.catalog.models import Course
from apps.content.models import Lesson


class AiChatSession(models.Model):
    CONTEXT_COURSE_TUTOR = "course_tutor"
    CONTEXT_CHOICES = [(CONTEXT_COURSE_TUTOR, "Course Tutor")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_chat_sessions"
    )
    # Nullable per the ERD, but every session created through
    # services.create_chat_session() sets this — a course-scoped tutor is
    # the only session type this milestone builds (a null course would be
    # an unscoped "ask about anything" session, which the security
    # checklist explicitly rules out).
    course = models.ForeignKey(
        Course, null=True, blank=True, on_delete=models.CASCADE, related_name="ai_chat_sessions"
    )
    context_type = models.CharField(
        max_length=30, choices=CONTEXT_CHOICES, default=CONTEXT_COURSE_TUTOR
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ai_chat_sessions"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user} / {self.course_id}"


class AiChatMessage(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_CHOICES = [(ROLE_USER, "User"), (ROLE_ASSISTANT, "Assistant")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AiChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    tokens_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_chat_messages"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["session", "created_at"])]

    def __str__(self):
        return f"{self.role}: {self.content[:30]}"


class AiGenerationJob(models.Model):
    JOB_SUMMARY = "summary"
    JOB_QUIZ = "quiz"
    JOB_FLASHCARDS = "flashcards"
    JOB_TRANSCRIPT = "transcript"
    JOB_SUBTITLES = "subtitles"
    JOB_TYPE_CHOICES = [
        (JOB_SUMMARY, "Summary"),
        (JOB_QUIZ, "Quiz"),
        (JOB_FLASHCARDS, "Flashcards"),
        (JOB_TRANSCRIPT, "Transcript"),
        (JOB_SUBTITLES, "Subtitles"),
    ]

    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_QUEUED, "Queued"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    # Polymorphic pointer (course/lesson/video), same pattern as
    # apps.payouts.Transaction.reference_type/reference_id — not a real FK
    # since the source model varies by job_type.
    source_type = models.CharField(max_length=30)
    source_id = models.UUIDField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_generation_jobs"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        db_table = "ai_generation_jobs"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.job_type} ({self.status})"


class AiGeneratedContent(models.Model):
    STATUS_READY = "ready"
    STATUS_CHOICES = [(STATUS_READY, "Ready")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.CharField(max_length=30)
    source_type = models.CharField(max_length=30)
    source_id = models.UUIDField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ai_generated_content",
    )
    content_payload = models.JSONField()
    model_used = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_READY)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_generated_content"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.content_type} for {self.source_type}:{self.source_id}"


class Flashcard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="flashcards")
    lesson = models.ForeignKey(
        Lesson, null=True, blank=True, on_delete=models.CASCADE, related_name="flashcards"
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="generated_flashcards"
    )
    front_text = models.TextField()
    back_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "flashcards"
        indexes = [models.Index(fields=["course", "lesson"])]
        ordering = ["-created_at"]

    def __str__(self):
        return self.front_text[:40]
