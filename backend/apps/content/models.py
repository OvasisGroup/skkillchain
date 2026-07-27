import uuid

from django.db import models

from apps.catalog.models import Course


class Section(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=200)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "sections"
        ordering = ["sort_order"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """
    lesson_type is currently a label only — quiz/assignment content lives in
    their own tables once the assessments app exists (M5); video metadata
    (provider, playback) is a deferred follow-up alongside the video
    provider adapter, per the M3 commit notes.
    """

    TYPE_VIDEO = "video"
    TYPE_ARTICLE = "article"
    TYPE_QUIZ = "quiz"
    TYPE_ASSIGNMENT = "assignment"
    TYPE_CHOICES = [
        (TYPE_VIDEO, "Video"),
        (TYPE_ARTICLE, "Article"),
        (TYPE_QUIZ, "Quiz"),
        (TYPE_ASSIGNMENT, "Assignment"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="lessons")
    lesson_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_VIDEO)
    title = models.CharField(max_length=200)
    sort_order = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)

    class Meta:
        db_table = "lessons"
        ordering = ["sort_order"]

    def __str__(self):
        return self.title
