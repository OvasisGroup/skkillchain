from django.conf import settings
from rest_framework.exceptions import PermissionDenied

from apps.learning.models import Enrollment

from . import anthropic_client
from .models import AiChatMessage, AiChatSession

TUTOR_MAX_TOKENS = 1024


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
