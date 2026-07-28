import uuid

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
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


@extend_schema(tags=["AI"])
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


@extend_schema(tags=["AI"])
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


@extend_schema(tags=["AI"], request=None, responses={200: AssignmentSubmissionSerializer})
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


@extend_schema(tags=["AI"], request=None, responses={202: AiGenerationJobSerializer})
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


@extend_schema(tags=["AI"], request=None, responses={202: AiGenerationJobSerializer})
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


@extend_schema(tags=["AI"], request=None, responses={202: AiGenerationJobSerializer})
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


@extend_schema(tags=["AI"], request=None, responses={202: AiGenerationJobSerializer})
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


@extend_schema(tags=["AI"], request=None, responses={202: AiGenerationJobSerializer})
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


@extend_schema(tags=["AI"])
class StudentFlashcardsListView(generics.ListAPIView):
    serializer_class = FlashcardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Flashcard.objects.filter(generated_by=self.request.user)
