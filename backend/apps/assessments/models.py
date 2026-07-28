import uuid

from django.conf import settings
from django.db import models

from apps.catalog.models import Course
from apps.content.models import Section


class Quiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="quizzes", null=True, blank=True
    )
    title = models.CharField(max_length=200)
    attempts_allowed = models.PositiveIntegerField(default=1)
    pass_score = models.PositiveIntegerField(default=70)  # percent, 0-100

    class Meta:
        db_table = "quizzes"

    def __str__(self):
        return self.title


class Question(models.Model):
    TYPE_SINGLE_CHOICE = "single_choice"
    TYPE_MULTIPLE_CHOICE = "multiple_choice"
    TYPE_CHOICES = [
        (TYPE_SINGLE_CHOICE, "Single choice"),
        (TYPE_MULTIPLE_CHOICE, "Multiple choice"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_SINGLE_CHOICE)
    prompt = models.TextField()
    explanation = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "questions"
        ordering = ["sort_order"]

    def __str__(self):
        return self.prompt[:60]


class Answer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "answers"
        ordering = ["sort_order"]

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_SUBMITTED = "submitted"
    STATUS_CHOICES = [(STATUS_IN_PROGRESS, "In progress"), (STATUS_SUBMITTED, "Submitted")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)  # percent
    passed = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = "quiz_attempts"
        ordering = ["-started_at"]
        constraints = [
            # A student can only have one attempt open at a time per quiz —
            # attempts_allowed is enforced against the count of *finished*
            # attempts, so a dangling in-progress one can't be used to farm
            # extra tries.
            models.UniqueConstraint(
                fields=["quiz", "student"],
                condition=models.Q(status="in_progress"),
                name="uniq_in_progress_attempt_per_student",
            )
        ]

    def __str__(self):
        return f"{self.student} attempt on {self.quiz}"


class QuizResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="responses")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="+")
    selected_answers = models.ManyToManyField(Answer, related_name="+", blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = "quiz_responses"
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"], name="uniq_response_per_question"
            )
        ]

    def __str__(self):
        return f"response to {self.question} in {self.attempt}"


class Assignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    instructions = models.TextField()
    # Flexible policy blob rather than fixed columns — e.g.
    # {"due_at": "2026-03-01T00:00:00Z", "allow_late": true}. Nothing reads
    # "allow_late" to block late submissions yet; grading is manual, so a
    # late submission is simply visible to the instructor as such.
    due_policy = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "assignments"

    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignment_submissions"
    )
    content_ref = models.TextField()  # a URL or free-text pointer to the submitted work
    grade = models.FloatField(null=True, blank=True)  # percent
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="graded_assignment_submissions",
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    # AI-suggested grading (M8) — deliberately separate from grade/
    # feedback/graded_by/graded_at above, which stay exclusively
    # human-authoritative. A suggestion here never reaches the real grade
    # fields except through the instructor's explicit
    # approve-ai-grade action (apps.assessments.views).
    ai_suggested_grade = models.FloatField(null=True, blank=True)
    ai_suggested_feedback = models.TextField(blank=True, default="")
    ai_suggested_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "assignment_submissions"
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "student"], name="uniq_submission_per_student"
            )
        ]

    def __str__(self):
        return f"{self.student} submission for {self.assignment}"


class CodingExercise(models.Model):
    # Only Python is actually judged today — see apps/assessments/judge.py.
    # The field stays generic (matching the documented schema's "language"
    # column) so adding a second judged language later is additive.
    LANGUAGE_PYTHON = "python"
    LANGUAGE_CHOICES = [(LANGUAGE_PYTHON, "Python 3")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="coding_exercises")
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="coding_exercises", null=True, blank=True
    )
    title = models.CharField(max_length=200)
    prompt = models.TextField()
    starter_code = models.TextField(blank=True)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default=LANGUAGE_PYTHON)
    time_limit_ms = models.PositiveIntegerField(default=2000)
    memory_limit_mb = models.PositiveIntegerField(default=256)

    class Meta:
        db_table = "coding_exercises"

    def __str__(self):
        return self.title


class CodingExerciseTestCase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coding_exercise = models.ForeignKey(
        CodingExercise, on_delete=models.CASCADE, related_name="test_cases"
    )
    input = models.TextField(blank=True)
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=True)
    weight = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "coding_exercise_test_cases"
        ordering = ["id"]

    def __str__(self):
        return f"test case for {self.coding_exercise}"


class CodingExerciseSubmission(models.Model):
    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_PASSED = "passed"
    STATUS_FAILED = "failed"
    STATUS_ERROR = "error"
    STATUS_CHOICES = [
        (STATUS_QUEUED, "Queued"),
        (STATUS_RUNNING, "Running"),
        (STATUS_PASSED, "Passed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_ERROR, "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coding_exercise = models.ForeignKey(
        CodingExercise, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coding_exercise_submissions",
    )
    source_code = models.TextField()
    language = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    score = models.FloatField(null=True, blank=True)  # percent, weighted by test-case weight
    runtime_ms = models.PositiveIntegerField(null=True, blank=True)
    # Per-test-case pass/fail. Hidden test cases never carry their
    # expected_output or the submission's actual stdout into this blob —
    # only {"is_hidden": true, "passed": bool} — so grading detail never
    # leaks a hidden test's answer back to the student.
    result_detail = models.JSONField(default=list, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "coding_exercise_submissions"
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student} submission for {self.coding_exercise}"
