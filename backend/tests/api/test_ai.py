from decimal import Decimal

import pytest

from apps.ai import anthropic_client
from apps.ai.anthropic_client import AIProviderError
from apps.ai.models import AiChatMessage, AiChatSession
from apps.catalog.models import Course
from apps.learning.models import Enrollment

pytestmark = pytest.mark.django_db


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


@pytest.fixture
def student(django_user_model):
    return django_user_model.objects.create_user(email="student@example.com", password="x")


@pytest.fixture
def student_client(api_client, student):
    api_client.force_authenticate(user=student)
    return api_client


@pytest.fixture
def course(instructor):
    c = Course.objects.create(
        owner=instructor,
        title="AI Course",
        summary="A course about AI.",
        description="Deep dive into AI.",
        price_amount=Decimal("10.00"),
    )
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


@pytest.fixture
def enrollment(student, course):
    return Enrollment.objects.create(student=student, course=course)


class TestTutorSessionCreate:
    def test_requires_enrollment(self, student_client, course):
        response = student_client.post(
            "/api/v1/ai/tutor/sessions/", {"course_id": str(course.id)}, format="json"
        )

        assert response.status_code == 403
        assert not AiChatSession.objects.filter(course=course).exists()

    def test_enrolled_student_can_start_session(self, student_client, course, enrollment):
        response = student_client.post(
            "/api/v1/ai/tutor/sessions/", {"course_id": str(course.id)}, format="json"
        )

        assert response.status_code == 201
        assert str(response.data["course"]) == str(course.id)

    def test_list_only_shows_own_sessions(self, student_client, student, course, enrollment):
        AiChatSession.objects.create(user=student, course=course)
        other = Course.objects.create(owner=course.owner, title="Other")
        from apps.identity.models import User

        other_user = User.objects.create_user(email="other@example.com", password="x")
        AiChatSession.objects.create(user=other_user, course=other)

        response = student_client.get("/api/v1/ai/tutor/sessions/")

        assert len(response.data["results"]) == 1


class TestTutorMessages:
    def test_send_message_calls_anthropic_and_persists_both_turns(
        self, student_client, student, course, enrollment, monkeypatch
    ):
        captured = {}

        def fake_send_message(system, user_message, *, model, max_tokens):
            captured["system"] = system
            captured["user_message"] = user_message
            captured["model"] = model
            return "The answer, scoped to this course, is 42."

        monkeypatch.setattr(anthropic_client, "send_message", fake_send_message)

        session = AiChatSession.objects.create(user=student, course=course)
        response = student_client.post(
            f"/api/v1/ai/tutor/sessions/{session.id}/messages/",
            {"body": "What is this course about?"},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["role"] == "assistant"
        assert response.data["content"] == "The answer, scoped to this course, is 42."
        assert captured["user_message"] == "What is this course about?"
        assert course.title in captured["system"]
        assert captured["model"] == "claude-sonnet-5"

        assert AiChatMessage.objects.filter(session=session, role="user").exists()
        assert AiChatMessage.objects.filter(session=session, role="assistant").exists()

    def test_non_owner_cannot_post_to_session(self, student_client, course, instructor):
        other_session = AiChatSession.objects.create(user=instructor, course=course)

        response = student_client.post(
            f"/api/v1/ai/tutor/sessions/{other_session.id}/messages/", {"body": "hi"}, format="json"
        )

        assert response.status_code == 403

    def test_ai_provider_error_becomes_400(
        self, student_client, student, course, enrollment, monkeypatch
    ):
        def boom(system, user_message, *, model, max_tokens):
            raise AIProviderError("no API key configured")

        monkeypatch.setattr(anthropic_client, "send_message", boom)

        session = AiChatSession.objects.create(user=student, course=course)
        response = student_client.post(
            f"/api/v1/ai/tutor/sessions/{session.id}/messages/", {"body": "hi"}, format="json"
        )

        assert response.status_code == 400
