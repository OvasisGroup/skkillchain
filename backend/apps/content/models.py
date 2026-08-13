import uuid

from django.core.validators import FileExtensionValidator
from django.db import models

from apps.catalog.models import Course

# content_file only ever holds video or PDF lesson content (see Lesson's
# docstring) — but the field itself had no extension allowlist, so any
# authenticated user with course-creation rights could upload an .html/.svg
# "lesson" that nginx then serves same-origin under /media/ on the API
# domain, a stored-XSS/malware-hosting foothold. Restricting to the file
# types the feature actually needs closes that off.
ALLOWED_LESSON_CONTENT_EXTENSIONS = ["mp4", "mov", "m4v", "webm", "pdf"]


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


def lesson_content_upload_path(instance, filename):
    return f"lessons/{instance.section_id}/{instance.id}/{filename}"


class Lesson(models.Model):
    """
    quiz/assignment content lives in their own tables in the assessments app
    (M5) — lesson_type is just a label for those two. video/pdf lessons hold
    their own file in content_file; video playback-position metadata beyond
    the raw file (provider, adaptive bitrate, etc.) is still a deferred
    follow-up per the M3 commit notes.
    """

    TYPE_VIDEO = "video"
    TYPE_PDF = "pdf"
    TYPE_ARTICLE = "article"
    TYPE_QUIZ = "quiz"
    TYPE_ASSIGNMENT = "assignment"
    TYPE_CHOICES = [
        (TYPE_VIDEO, "Video"),
        (TYPE_PDF, "PDF"),
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
    # Only meaningful for TYPE_VIDEO/TYPE_PDF; blank for article/quiz/assignment.
    # max_length=255 (Django's FileField default is 100): the upload path is
    # "lessons/<section-uuid>/<lesson-uuid>/<filename>" — the two UUIDs alone
    # take 82 characters, so 100 left almost no room for a real filename and
    # made Storage.get_available_name() fail outright on realistic names.
    content_file = models.FileField(
        upload_to=lesson_content_upload_path,
        blank=True,
        max_length=255,
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_LESSON_CONTENT_EXTENSIONS)],
    )

    class Meta:
        db_table = "lessons"
        ordering = ["sort_order"]

    def __str__(self):
        return self.title
