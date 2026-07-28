import uuid

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessments.models import AssignmentSubmission
from apps.assessments.serializers import AssignmentSubmissionSerializer
from apps.catalog.models import Course
from apps.content.models import Lesson
from apps.learning.models import Enrollment
from shared.api.pagination import StartedAtCursorPagination

from . import services
from .anthropic_client import AIProviderError
from .models import AiChatMessage, AiChatSession, AiGenerationJob, Flashcard
from .serializers import (
    AiChatMessageCreateSerializer,
    AiChatMessageSerializer,
    AiChatSessionCreateSerializer,
    AiChatSessionSerializer,
    AiGenerationJobSerializer,
    FlashcardSerializer,
)


def _own_session_or_403(user, session_id) -> AiChatSession:
    session = get_object_or_404(AiChatSession, id=session_id)
    if session.user_id != user.id:
        raise PermissionDenied("You can only access your own tutor sessions.")
    return session


def _owned_course_or_403(course_id, user) -> Course:
    course = get_object_or_404(Course, pk=course_id)
    if course.owner_id != user.id:
        raise PermissionDenied("You do not own this course.")
    return course


def _enrolled_lesson_or_403(lesson_id, user) -> Lesson:
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    course_id = lesson.section.course_id
    if not Enrollment.objects.filter(course_id=course_id, student=user).exists():
        raise PermissionDenied("You must be enrolled in this lesson's course.")
    return lesson


_AI_SESSION_EXAMPLE = {
    "id": "a1b2c3d4-...",
    "course": "1c2d3e4f-...",
    "context_type": "course",
    "started_at": "2026-02-01T10:00:00Z",
    "ended_at": None,
}


@extend_schema_view(
    get=extend_schema(
        tags=["AI"],
        description="Lists the current user's AI tutor chat sessions.",
        examples=[OpenApiExample("Session", value=_AI_SESSION_EXAMPLE, response_only=True)],
    ),
    post=extend_schema(
        tags=["AI"],
        description="Starts a new AI tutor chat session scoped to a course.",
        examples=[
            OpenApiExample(
                "Start session",
                value={"course_id": "1c2d3e4f-5a6b-7c8d-9e0f-1a2b3c4d5e6f"},
                request_only=True,
            ),
            OpenApiExample("Created", value=_AI_SESSION_EXAMPLE, response_only=True),
        ],
    ),
)
class AiTutorSessionCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StartedAtCursorPagination

    def get_serializer_class(self):
        return (
            AiChatSessionCreateSerializer
            if self.request.method == "POST"
            else AiChatSessionSerializer
        )

    def get_queryset(self):
        return AiChatSession.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = get_object_or_404(Course, id=serializer.validated_data["course_id"])
        session = services.create_chat_session(request.user, course)
        return Response(AiChatSessionSerializer(session).data, status=201)


@extend_schema_view(
    get=extend_schema(
        tags=["AI"],
        description="Lists messages in an AI tutor chat session the current user owns.",
        examples=[
            OpenApiExample(
                "Message",
                value={
                    "id": "b2c3d4e5-...",
                    "session": "a1b2c3d4-...",
                    "role": "assistant",
                    "content": "List comprehensions build a list in one expression...",
                    "tokens_used": 128,
                    "created_at": "2026-02-01T10:01:00Z",
                },
                response_only=True,
            )
        ],
    ),
    post=extend_schema(
        tags=["AI"],
        description="Sends a message to the AI tutor within a session the current user owns "
        "and returns its reply.",
        examples=[
            OpenApiExample(
                "Ask",
                value={"body": "What's the difference between a list and a generator?"},
                request_only=True,
            )
        ],
    ),
)
class AiTutorMessageCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai-chat"

    def get_serializer_class(self):
        return (
            AiChatMessageCreateSerializer
            if self.request.method == "POST"
            else AiChatMessageSerializer
        )

    def get_queryset(self):
        session = _own_session_or_403(self.request.user, self.kwargs["session_id"])
        return AiChatMessage.objects.filter(session=session)

    def create(self, request, *args, **kwargs):
        session = _own_session_or_403(request.user, self.kwargs["session_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            reply = services.send_chat_message(
                session, request.user, serializer.validated_data["body"]
            )
        except AIProviderError as exc:
            raise ValidationError(f"AI tutor request failed: {exc}") from exc
        return Response(AiChatMessageSerializer(reply).data, status=201)


@extend_schema(
    tags=["AI"],
    request=None,
    responses={200: AssignmentSubmissionSerializer},
    description="Generates an AI grade suggestion for an assignment submission — writes only "
    "ai_suggested_grade/ai_suggested_feedback, never grade/feedback directly. An instructor "
    "must explicitly approve it via POST .../approve-ai-grade/ (or edit it via the manual "
    "grade endpoint) before it counts as the real grade.",
    examples=[
        OpenApiExample(
            "Suggestion",
            value={
                "id": "c3d4e5f6-...",
                "assignment": "a1b2c3d4-...",
                "student_email": "student@example.com",
                "content_ref": "https://github.com/student/final-project",
                "grade": None,
                "feedback": "",
                "graded_at": None,
                "submitted_at": "2026-01-30T12:00:00Z",
                "ai_suggested_grade": 88,
                "ai_suggested_feedback": "Solid implementation, minor style nits.",
                "ai_suggested_at": "2026-01-31T09:00:00Z",
            },
            response_only=True,
        )
    ],
)
class AIAssignmentGradeSuggestionView(APIView):
    """Generates an AI grade *suggestion* only — see
    apps.ai.services.suggest_assignment_grade and
    apps.assessments.views.AssignmentSubmissionApproveAIGradeView, which is
    the only path from suggestion to a real grade."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai-generation"

    def post(self, request, submission_id):
        submission = get_object_or_404(AssignmentSubmission, pk=submission_id)
        _owned_course_or_403(submission.assignment.course_id, request.user)
        try:
            services.suggest_assignment_grade(submission)
        except AIProviderError as exc:
            raise ValidationError(f"AI grading request failed: {exc}") from exc
        return Response(AssignmentSubmissionSerializer(submission).data)


_AI_JOB_EXAMPLE = {
    "id": "d4e5f6a7-...",
    "job_type": "quiz",
    "source_type": "course",
    "source_id": "1c2d3e4f-...",
    "status": "queued",
    "started_at": None,
    "completed_at": None,
    "error_message": "",
}


@extend_schema(
    tags=["AI"],
    request=None,
    responses={202: AiGenerationJobSerializer},
    description="Queues an AI job to draft a quiz for a course the current instructor owns. "
    "The job runs asynchronously (Celery) — this response reflects the queued state only; "
    "there is no polling endpoint yet, so failures (captured in error_message) surface "
    "through whatever downstream effect the job was meant to have, not a status check here.",
    examples=[OpenApiExample("Queued", value=_AI_JOB_EXAMPLE, response_only=True)],
)
class AiCourseGenerateQuizView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai-generation"

    def post(self, request, course_id):
        course = _owned_course_or_403(course_id, request.user)
        job = services.enqueue_generation_job(
            request.user,
            job_type=AiGenerationJob.JOB_QUIZ,
            source_type="course",
            source_id=course.id,
        )
        return Response(AiGenerationJobSerializer(job).data, status=202)


@extend_schema(
    tags=["AI"],
    request=None,
    responses={202: AiGenerationJobSerializer},
    description="Queues an AI job to summarize a lesson for an enrolled student.",
    examples=[
        OpenApiExample(
            "Queued",
            value={**_AI_JOB_EXAMPLE, "job_type": "summary", "source_type": "lesson"},
            response_only=True,
        )
    ],
)
class AiLessonGenerateSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai-generation"

    def post(self, request, lesson_id):
        lesson = _enrolled_lesson_or_403(lesson_id, request.user)
        job = services.enqueue_generation_job(
            request.user,
            job_type=AiGenerationJob.JOB_SUMMARY,
            source_type="lesson",
            source_id=lesson.id,
        )
        return Response(AiGenerationJobSerializer(job).data, status=202)


@extend_schema(
    tags=["AI"],
    request=None,
    responses={202: AiGenerationJobSerializer},
    description="Queues an AI job to generate flashcards for a lesson for an enrolled "
    "student — results appear via GET /students/me/flashcards/ once the job completes.",
    examples=[
        OpenApiExample(
            "Queued",
            value={**_AI_JOB_EXAMPLE, "job_type": "flashcards", "source_type": "lesson"},
            response_only=True,
        )
    ],
)
class AiLessonGenerateFlashcardsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai-generation"

    def post(self, request, lesson_id):
        lesson = _enrolled_lesson_or_403(lesson_id, request.user)
        job = services.enqueue_generation_job(
            request.user,
            job_type=AiGenerationJob.JOB_FLASHCARDS,
            source_type="lesson",
            source_id=lesson.id,
        )
        return Response(AiGenerationJobSerializer(job).data, status=202)


@extend_schema(
    tags=["AI"],
    request=None,
    responses={202: AiGenerationJobSerializer},
    description="Queues a video transcript generation job. No video/audio asset storage "
    "exists in this codebase yet (a deferred follow-up — see Lesson's own docstring), so the "
    "job is accepted and queued like any other but fails immediately with a clear "
    "error_message rather than fabricating a transcript.",
    examples=[
        OpenApiExample(
            "Queued",
            value={**_AI_JOB_EXAMPLE, "job_type": "transcript", "source_type": "video"},
            response_only=True,
        )
    ],
)
class AiVideoGenerateTranscriptView(APIView):
    """No video/audio asset model exists anywhere in this codebase yet
    (see apps.content.models.Lesson's own docstring) — the job is
    accepted and queued like any other, but fails immediately with a
    clear error_message rather than fabricating a transcript."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai-generation"

    def post(self, request, video_id: uuid.UUID):
        job = services.enqueue_generation_job(
            request.user,
            job_type=AiGenerationJob.JOB_TRANSCRIPT,
            source_type="video",
            source_id=video_id,
        )
        return Response(AiGenerationJobSerializer(job).data, status=202)


@extend_schema(
    tags=["AI"],
    request=None,
    responses={202: AiGenerationJobSerializer},
    description="Queues a video subtitles generation job. Same source-content gap as "
    "POST .../generate-transcript/ — no video asset exists yet, so the job fails immediately "
    "with a clear error_message.",
    examples=[
        OpenApiExample(
            "Queued",
            value={**_AI_JOB_EXAMPLE, "job_type": "subtitles", "source_type": "video"},
            response_only=True,
        )
    ],
)
class AiVideoGenerateSubtitlesView(APIView):
    """Same source-content gap as AiVideoGenerateTranscriptView above."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai-generation"

    def post(self, request, video_id: uuid.UUID):
        job = services.enqueue_generation_job(
            request.user,
            job_type=AiGenerationJob.JOB_SUBTITLES,
            source_type="video",
            source_id=video_id,
        )
        return Response(AiGenerationJobSerializer(job).data, status=202)


@extend_schema(
    tags=["AI"],
    description="Lists AI-generated flashcards owned by the current user.",
    examples=[
        OpenApiExample(
            "Flashcard",
            value={
                "id": "e5f6a7b8-...",
                "course": "1c2d3e4f-...",
                "lesson": "d1e2f3a4-...",
                "front_text": "What does len() return for an empty list?",
                "back_text": "0",
                "created_at": "2026-02-01T11:00:00Z",
            },
            response_only=True,
        )
    ],
)
class StudentFlashcardsListView(generics.ListAPIView):
    serializer_class = FlashcardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Flashcard.objects.filter(generated_by=self.request.user)
