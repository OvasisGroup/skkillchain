import json

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.learning.models import Enrollment

from . import anthropic_client
from .anthropic_client import AIProviderError
from .models import AiChatMessage, AiChatSession, AiGeneratedContent, AiGenerationJob, Flashcard

TUTOR_MAX_TOKENS = 1024
GRADE_SUGGESTION_MAX_TOKENS = 1024
GENERATION_MAX_TOKENS = 2048


def _has_any_enrollment(user, course_id) -> bool:
    return Enrollment.objects.filter(course_id=course_id, student=user).exists()


def _course_system_prompt(course) -> str:
    return (
        f"You are an AI tutor for the course \"{course.title}\".\n"
        f"Course summary: {course.summary}\n"
        f"Course description: {course.description}\n\n"
        "Only answer questions about this course's own content. If asked "
        "about an unrelated course, another product, or the platform's "
        "internal workings, politely decline and redirect the student to "
        "this course's material."
    )


def create_chat_session(user, course) -> AiChatSession:
    # "AI tutor sessions are scoped to the enrolled course's own content"
    # per docs/07-delivery-planning/02-backend-build-milestones.md M8 —
    # any enrollment status counts, same gate as course discussions.
    if not _has_any_enrollment(user, course.id):
        raise PermissionDenied("You must be enrolled in this course to start a tutor session.")
    return AiChatSession.objects.create(user=user, course=course)


def send_chat_message(session: AiChatSession, user, body: str) -> AiChatMessage:
    AiChatMessage.objects.create(session=session, role=AiChatMessage.ROLE_USER, content=body)

    reply_text = anthropic_client.send_message(
        _course_system_prompt(session.course),
        body,
        model=settings.AI_CHAT_MODEL,
        max_tokens=TUTOR_MAX_TOKENS,
    )

    return AiChatMessage.objects.create(
        session=session, role=AiChatMessage.ROLE_ASSISTANT, content=reply_text
    )


_GRADE_SUGGESTION_SYSTEM_PROMPT = (
    "You are grading a student's assignment submission for an instructor's "
    "review. Respond with ONLY a JSON object of the exact shape "
    '{"grade": <number 0-100>, "feedback": "<string>"} — no other text.'
)


def suggest_assignment_grade(submission):
    """Calls Claude for a grade suggestion and writes it to
    ai_suggested_grade/ai_suggested_feedback/ai_suggested_at only — this
    function never touches grade/feedback/graded_by/graded_at, which stay
    human-authoritative until an instructor calls
    apps.assessments.views.AssignmentSubmissionApproveAIGradeView."""
    assignment = submission.assignment
    user_message = (
        f"Assignment: {assignment.title}\n"
        f"Instructions: {assignment.instructions}\n\n"
        f"Student submission: {submission.content_ref}"
    )

    reply_text = anthropic_client.send_message(
        _GRADE_SUGGESTION_SYSTEM_PROMPT,
        user_message,
        model=settings.AI_GENERATION_MODEL,
        max_tokens=GRADE_SUGGESTION_MAX_TOKENS,
    )

    try:
        parsed = json.loads(reply_text)
        grade = float(parsed["grade"])
        feedback = str(parsed["feedback"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise AIProviderError("Model did not return a valid grade suggestion.") from exc

    submission.ai_suggested_grade = grade
    submission.ai_suggested_feedback = feedback
    submission.ai_suggested_at = timezone.now()
    submission.save(update_fields=["ai_suggested_grade", "ai_suggested_feedback", "ai_suggested_at"])
    return submission


class NoSourceContentError(AIProviderError):
    """Raised for job types with no real source content to generate
    from — transcript/subtitle generation, since no video/audio asset
    model exists anywhere in this codebase yet (apps.content.Lesson's own
    docstring already flags video metadata as a deferred follow-up).
    Caught the same way as any other AIProviderError."""


def enqueue_generation_job(user, *, job_type: str, source_type: str, source_id) -> AiGenerationJob:
    from . import tasks

    job = AiGenerationJob.objects.create(
        job_type=job_type, source_type=source_type, source_id=source_id, requested_by=user
    )
    tasks.dispatch_generation_job.delay(str(job.id))
    return job


def _generate_summary_content(lesson) -> str:
    course = lesson.section.course
    system = "You write concise lesson summaries for students."
    # Lessons in this schema carry only a title/type/duration — no body or
    # transcript text exists to summarize (video asset storage is a
    # deferred follow-up per apps.content.models.Lesson's own docstring) —
    # so this is a best-effort summary from the title and course context,
    # not a summary of real lesson content.
    user_message = (
        f"Course: {course.title}\n"
        f"Course summary: {course.summary}\n"
        f"Lesson title: {lesson.title} ({lesson.get_lesson_type_display()})\n\n"
        "Write a short (3-5 sentence) summary of what a student would "
        "likely learn from this lesson, based on its title and the "
        "course it belongs to."
    )
    return anthropic_client.send_message(
        system, user_message, model=settings.AI_GENERATION_MODEL, max_tokens=GENERATION_MAX_TOKENS
    )


def _generate_quiz_content(course) -> list[dict]:
    system = (
        "You write multiple-choice quiz questions for an online course. "
        "Respond with ONLY a JSON array of objects shaped like "
        '{"question": "...", "options": ["...", "...", "...", "..."], '
        '"correct_index": 0} — no other text.'
    )
    user_message = (
        f"Course: {course.title}\n"
        f"Summary: {course.summary}\n"
        f"Description: {course.description}\n\n"
        "Write 5 quiz questions covering this course's likely content."
    )
    reply_text = anthropic_client.send_message(
        system, user_message, model=settings.AI_GENERATION_MODEL, max_tokens=GENERATION_MAX_TOKENS
    )
    try:
        questions = json.loads(reply_text)
        if not isinstance(questions, list):
            raise ValueError("expected a JSON array")
    except (json.JSONDecodeError, ValueError) as exc:
        raise AIProviderError("Model did not return valid quiz JSON.") from exc
    return questions


def _generate_flashcards_content(lesson) -> list[dict]:
    course = lesson.section.course
    system = (
        "You write flashcards (front/back) for students studying a "
        'lesson. Respond with ONLY a JSON array of objects shaped like '
        '{"front": "...", "back": "..."} — no other text.'
    )
    user_message = (
        f"Course: {course.title}\n"
        f"Lesson title: {lesson.title}\n\n"
        "Write 5 flashcards testing understanding of this lesson's "
        "likely topic."
    )
    reply_text = anthropic_client.send_message(
        system, user_message, model=settings.AI_GENERATION_MODEL, max_tokens=GENERATION_MAX_TOKENS
    )
    try:
        cards = json.loads(reply_text)
        if not isinstance(cards, list):
            raise ValueError("expected a JSON array")
    except (json.JSONDecodeError, ValueError) as exc:
        raise AIProviderError("Model did not return valid flashcard JSON.") from exc
    return cards


def run_generation_job(job: AiGenerationJob) -> None:
    """The actual per-job-type generation logic. Kept separate from
    tasks.dispatch_generation_job so it's directly unit-testable without
    going through Celery."""
    from apps.catalog.models import Course
    from apps.content.models import Lesson

    if job.job_type == AiGenerationJob.JOB_SUMMARY:
        lesson = Lesson.objects.get(id=job.source_id)
        summary_text = _generate_summary_content(lesson)
        AiGeneratedContent.objects.create(
            content_type="summary",
            source_type=job.source_type,
            source_id=job.source_id,
            user=job.requested_by,
            content_payload={"summary": summary_text},
            model_used=settings.AI_GENERATION_MODEL,
        )
    elif job.job_type == AiGenerationJob.JOB_QUIZ:
        course = Course.objects.get(id=job.source_id)
        questions = _generate_quiz_content(course)
        AiGeneratedContent.objects.create(
            content_type="quiz",
            source_type=job.source_type,
            source_id=job.source_id,
            user=job.requested_by,
            content_payload={"questions": questions},
            model_used=settings.AI_GENERATION_MODEL,
        )
    elif job.job_type == AiGenerationJob.JOB_FLASHCARDS:
        lesson = Lesson.objects.get(id=job.source_id)
        course = lesson.section.course
        cards = _generate_flashcards_content(lesson)
        try:
            Flashcard.objects.bulk_create(
                [
                    Flashcard(
                        course=course,
                        lesson=lesson,
                        generated_by=job.requested_by,
                        front_text=card["front"],
                        back_text=card["back"],
                    )
                    for card in cards
                ]
            )
        except (KeyError, TypeError) as exc:
            raise AIProviderError("Model returned malformed flashcard entries.") from exc
    elif job.job_type in (AiGenerationJob.JOB_TRANSCRIPT, AiGenerationJob.JOB_SUBTITLES):
        raise NoSourceContentError(
            "No source audio/video content is available for this platform "
            "yet — video asset storage is a deferred follow-up."
        )
    else:
        raise AIProviderError(f"Unknown job_type: {job.job_type}")
