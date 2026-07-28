import json
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.ai import anthropic_client, tasks
from apps.ai.anthropic_client import AIProviderError
from apps.ai.models import AiGenerationJob, Flashcard
from apps.assessments.models import Assignment, AssignmentSubmission
from apps.catalog.models import Course
from apps.content.models import Lesson, Section
from apps.learning.models import Enrollment

pytestmark = pytest.mark.django_db


def _client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


@pytest.fixture
def instructor_client(api_client, instructor):
    api_client.force_authenticate(user=instructor)
    return api_client


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
        owner=instructor, title="Gen Course", summary="s", description="d", price_amount=Decimal("10.00")
    )
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


@pytest.fixture
def enrollment(student, course):
    return Enrollment.objects.create(student=student, course=course)


@pytest.fixture
def lesson(course):
    section = Section.objects.create(course=course, title="Section 1")
    return Lesson.objects.create(section=section, title="Lesson 1")


@pytest.fixture
def assignment(course):
    return Assignment.objects.create(course=course, title="Essay", instructions="Write 500 words.")


@pytest.fixture
def submission(assignment, student):
    return AssignmentSubmission.objects.create(
        assignment=assignment, student=student, content_ref="https://example.com/essay.pdf"
    )


class TestGenerationJobEndpoints:
    def test_generate_quiz_requires_course_ownership(self, student_client, course):
        response = student_client.post(f"/api/v1/ai/courses/{course.id}/generate-quiz/")

        assert response.status_code == 403

    def test_generate_quiz_enqueues_job(self, instructor_client, course):
        response = instructor_client.post(f"/api/v1/ai/courses/{course.id}/generate-quiz/")

        assert response.status_code == 202
        assert response.data["status"] == "queued"
        assert AiGenerationJob.objects.filter(job_type="quiz", source_id=course.id).exists()

    def test_generate_summary_requires_enrollment(self, instructor_client, lesson):
        response = instructor_client.post(f"/api/v1/ai/lessons/{lesson.id}/generate-summary/")

        assert response.status_code == 403

    def test_generate_summary_enrolled_ok(self, student_client, lesson, enrollment):
        response = student_client.post(f"/api/v1/ai/lessons/{lesson.id}/generate-summary/")

        assert response.status_code == 202

    def test_generate_transcript_has_no_source_gate_but_fails_when_run(
        self, student_client, monkeypatch
    ):
        import uuid

        video_id = uuid.uuid4()
        response = student_client.post(f"/api/v1/ai/videos/{video_id}/generate-transcript/")

        assert response.status_code == 202
        job = AiGenerationJob.objects.get(id=response.data["id"])

        tasks.dispatch_generation_job(str(job.id))
        job.refresh_from_db()
        assert job.status == "failed"
        assert "no source" in job.error_message.lower()


class TestRunGenerationJob:
    def test_quiz_job_persists_generated_content(self, instructor, course, monkeypatch):
        from apps.ai.models import AiGeneratedContent

        def fake_send_message(system, user_message, *, model, max_tokens):
            return json.dumps(
                [{"question": "Q1?", "options": ["a", "b"], "correct_index": 0}]
            )

        monkeypatch.setattr(anthropic_client, "send_message", fake_send_message)

        job = AiGenerationJob.objects.create(
            job_type=AiGenerationJob.JOB_QUIZ, source_type="course", source_id=course.id, requested_by=instructor
        )
        tasks.dispatch_generation_job(str(job.id))

        job.refresh_from_db()
        assert job.status == "completed"
        content = AiGeneratedContent.objects.get(source_id=course.id, content_type="quiz")
        assert content.content_payload["questions"][0]["question"] == "Q1?"

    def test_flashcards_job_persists_flashcard_rows(self, instructor, course, lesson, monkeypatch):
        def fake_send_message(system, user_message, *, model, max_tokens):
            return json.dumps([{"front": "F1", "back": "B1"}, {"front": "F2", "back": "B2"}])

        monkeypatch.setattr(anthropic_client, "send_message", fake_send_message)

        job = AiGenerationJob.objects.create(
            job_type=AiGenerationJob.JOB_FLASHCARDS,
            source_type="lesson",
            source_id=lesson.id,
            requested_by=instructor,
        )
        tasks.dispatch_generation_job(str(job.id))

        job.refresh_from_db()
        assert job.status == "completed"
        assert Flashcard.objects.filter(lesson=lesson).count() == 2

    def test_bad_json_from_model_marks_job_failed(self, instructor, course, monkeypatch):
        monkeypatch.setattr(anthropic_client, "send_message", lambda *a, **k: "not json")

        job = AiGenerationJob.objects.create(
            job_type=AiGenerationJob.JOB_QUIZ, source_type="course", source_id=course.id, requested_by=instructor
        )
        tasks.dispatch_generation_job(str(job.id))

        job.refresh_from_db()
        assert job.status == "failed"
        assert job.error_message


class TestAIGradeSuggestionAndApproval:
    def test_suggest_grade_writes_only_suggested_fields(
        self, instructor_client, submission, monkeypatch
    ):
        monkeypatch.setattr(
            anthropic_client,
            "send_message",
            lambda *a, **k: json.dumps({"grade": 88, "feedback": "Good work."}),
        )

        response = instructor_client.post(f"/api/v1/ai/assignments/{submission.id}/grade/")

        assert response.status_code == 200
        submission.refresh_from_db()
        assert submission.ai_suggested_grade == 88
        assert submission.ai_suggested_feedback == "Good work."
        assert submission.grade is None
        assert submission.graded_by is None

    def test_cannot_approve_without_a_suggestion(self, instructor_client, submission):
        response = instructor_client.post(
            f"/api/v1/assignments/submissions/{submission.id}/approve-ai-grade/"
        )

        assert response.status_code == 400

    def test_approve_copies_suggestion_into_real_grade(
        self, instructor_client, instructor, submission, monkeypatch
    ):
        monkeypatch.setattr(
            anthropic_client,
            "send_message",
            lambda *a, **k: json.dumps({"grade": 75, "feedback": "Solid."}),
        )
        instructor_client.post(f"/api/v1/ai/assignments/{submission.id}/grade/")

        response = instructor_client.post(
            f"/api/v1/assignments/submissions/{submission.id}/approve-ai-grade/"
        )

        assert response.status_code == 200
        submission.refresh_from_db()
        assert submission.grade == 75
        assert submission.feedback == "Solid."
        assert submission.graded_by == instructor
        assert submission.graded_at is not None

    def test_non_owner_cannot_suggest_grade(self, student_client, submission):
        response = student_client.post(f"/api/v1/ai/assignments/{submission.id}/grade/")

        assert response.status_code == 403

    def test_provider_error_returns_400(self, instructor_client, submission, monkeypatch):
        def boom(*a, **k):
            raise AIProviderError("down")

        monkeypatch.setattr(anthropic_client, "send_message", boom)

        response = instructor_client.post(f"/api/v1/ai/assignments/{submission.id}/grade/")

        assert response.status_code == 400
