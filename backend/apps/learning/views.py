from django.db.models import Max
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.services import record_analytics_event
from apps.audit.services import record_event
from apps.catalog.models import Course
from apps.content.models import Lesson, Section
from shared.api.pagination import EnrolledAtCursorPagination, IssuedAtCursorPagination

from .certificates import ensure_certificate_pdf
from .models import (
    Certificate,
    Enrollment,
    ProgressTracking,
    RecentlyViewed,
    Wishlist,
    WishlistItem,
)
from .serializers import (
    BookmarkCreateSerializer,
    CertificateSerializer,
    CertificateVerifyResponseSerializer,
    CurriculumSectionSerializer,
    EnrollmentProgressSerializer,
    EnrollmentSerializer,
    EnrollRequestSerializer,
    LessonContentSerializer,
    LessonNoteCreateSerializer,
    ProgressEntrySerializer,
    ProgressUpdateSerializer,
    WishlistItemSerializer,
)
from .services import maybe_complete_enrollment


def _enrollment_for_course_or_403(user, course_id):
    enrollment = Enrollment.objects.filter(student=user, course_id=course_id).first()
    if enrollment is None:
        raise PermissionDenied("You must be enrolled in this course.")
    return enrollment


def _enrollment_for_lesson_or_404(user, lesson):
    enrollment = Enrollment.objects.filter(student=user, course_id=lesson.section.course_id).first()
    if enrollment is None:
        raise PermissionDenied("You must be enrolled in this course.")
    return enrollment


_ENROLLMENT_EXAMPLE = {
    "id": "d4e5f6a7-...",
    "course": {
        "id": "1c2d3e4f-...",
        "title": "Complete Python Bootcamp",
        "slug": "complete-python-bootcamp",
        "summary": "Learn Python from scratch, from syntax to real projects.",
    },
    "source": "direct",
    "status": "active",
    "enrolled_at": "2026-01-16T10:00:00Z",
    "completed_at": None,
}


@extend_schema(
    tags=["Student"],
    request=EnrollRequestSerializer,
    responses={201: EnrollmentSerializer},
    description="Enrolls the current user in a published course (free courses, or courses "
    "already paid for via checkout). Fails with 400 if already enrolled.",
    examples=[
        OpenApiExample(
            "Enroll",
            value={"course_id": "1c2d3e4f-5a6b-7c8d-9e0f-1a2b3c4d5e6f"},
            request_only=True,
        ),
        OpenApiExample("Enrolled", value=_ENROLLMENT_EXAMPLE, response_only=True),
    ],
)
class EnrollView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = EnrollRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course = get_object_or_404(
            Course, pk=serializer.validated_data["course_id"], status=Course.STATUS_PUBLISHED
        )
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            raise ValidationError("Already enrolled in this course.")

        enrollment = Enrollment.objects.create(student=request.user, course=course)
        record_event(
            actor=request.user,
            action="enrollment.create",
            entity_type="Enrollment",
            entity_id=enrollment.id,
            request=request,
            payload={"course_id": str(course.id)},
        )
        record_analytics_event("enrollment.created", actor=request.user, course=course)
        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Student"],
    description="Lists all of the current user's course enrollments, most recent first.",
    examples=[OpenApiExample("Enrollment", value=_ENROLLMENT_EXAMPLE, response_only=True)],
)
class MyCoursesView(generics.ListAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = EnrolledAtCursorPagination

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user).select_related("course")


@extend_schema(
    tags=["Student"],
    description="Lists the current user's active enrollments ordered by most recent lesson "
    "activity — for a 'continue learning' shelf on the student dashboard.",
    examples=[OpenApiExample("Enrollment", value=_ENROLLMENT_EXAMPLE, response_only=True)],
)
class ContinueLearningView(generics.ListAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    # Not cursor-paginated: ordering is by an annotated aggregate
    # (most-recent lesson activity), which cursor pagination can't page
    # through consistently — and a student's *active* enrollment count is
    # small enough that a plain list is the right tool here anyway.
    pagination_class = None

    def get_queryset(self):
        return (
            Enrollment.objects.filter(student=self.request.user, status=Enrollment.STATUS_ACTIVE)
            .select_related("course")
            .annotate(last_activity=Max("progress_entries__last_viewed_at"))
            .order_by("-last_activity", "-enrolled_at")
        )


@extend_schema(
    tags=["Student"],
    responses={200: CurriculumSectionSerializer(many=True)},
    description="Gets the section/lesson structure for a course the current user is enrolled "
    "in — no lesson content, just what's needed to build a curriculum sidebar.",
)
class CourseCurriculumView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_id):
        _enrollment_for_course_or_403(request.user, course_id)
        sections = Section.objects.filter(course_id=course_id).prefetch_related("lessons")
        return Response(CurriculumSectionSerializer(sections, many=True).data)


@extend_schema(
    tags=["Student"],
    responses={200: LessonContentSerializer},
    description="Gets a lesson's playable/viewable content (video or PDF file URL) for a "
    "course the current user is enrolled in.",
)
class LessonContentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        lesson = get_object_or_404(Lesson, pk=id)
        _enrollment_for_lesson_or_404(request.user, lesson)
        return Response(LessonContentSerializer(lesson, context={"request": request}).data)


@extend_schema(
    tags=["Student"],
    description="Lists the courses the current user has wishlisted.",
    examples=[
        OpenApiExample(
            "Wishlist item",
            value={
                "course": {
                    "id": "1c2d3e4f-...",
                    "title": "Complete Python Bootcamp",
                    "slug": "complete-python-bootcamp",
                    "summary": "Learn Python from scratch, from syntax to real projects.",
                },
                "added_at": "2026-01-14T08:00:00Z",
            },
            response_only=True,
        )
    ],
)
class WishlistView(generics.ListAPIView):
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist.items.select_related("course")


class WishlistItemAddRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Student"],
        request=None,
        responses={201: None, 200: None},
        description="Adds a published course to the current user's wishlist. Returns 200 "
        "(not 201) if it was already there.",
    )
    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id, status=Course.STATUS_PUBLISHED)
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        _, created = WishlistItem.objects.get_or_create(wishlist=wishlist, course=course)
        return Response(status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @extend_schema(
        tags=["Student"],
        responses={204: None},
        description="Removes a course from the current user's wishlist. 404 if it wasn't "
        "wishlisted.",
    )
    def delete(self, request, course_id):
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        deleted, _ = WishlistItem.objects.filter(wishlist=wishlist, course_id=course_id).delete()
        if not deleted:
            raise NotFound("Not in your wishlist.")
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Progress"],
    request=ProgressUpdateSerializer,
    responses={200: ProgressEntrySerializer},
    description="Records playback/reading progress for one lesson. If this brings every "
    "lesson in the course to 100%, the enrollment is marked complete and a certificate is "
    "issued automatically.",
    examples=[
        OpenApiExample(
            "Update progress",
            value={
                "lesson_id": "d1e2f3a4-...",
                "percent_complete": 75,
                "last_position_seconds": 420,
            },
            request_only=True,
        ),
        OpenApiExample(
            "Progress recorded",
            value={
                "lesson_id": "d1e2f3a4-...",
                "lesson_title": "Welcome",
                "percent_complete": 75,
                "last_position_seconds": 420,
                "last_viewed_at": "2026-01-16T11:00:00Z",
            },
            response_only=True,
        ),
    ],
)
class ProgressUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lesson = get_object_or_404(Lesson, pk=data["lesson_id"])
        enrollment = _enrollment_for_lesson_or_404(request.user, lesson)

        entry, _ = ProgressTracking.objects.update_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={
                "percent_complete": data["percent_complete"],
                "last_position_seconds": data["last_position_seconds"],
            },
        )
        RecentlyViewed.objects.update_or_create(user=request.user, course=lesson.section.course)
        record_analytics_event(
            "lesson.progress",
            actor=request.user,
            course=lesson.section.course,
            payload={
                "lesson_id": str(lesson.id),
                "percent_complete": data["percent_complete"],
                "last_position_seconds": data["last_position_seconds"],
            },
        )

        certificate = maybe_complete_enrollment(enrollment)
        if certificate is not None:
            record_analytics_event(
                "enrollment.completed", actor=request.user, course=lesson.section.course
            )
            record_event(
                actor=request.user,
                action="enrollment.complete",
                entity_type="Enrollment",
                entity_id=enrollment.id,
                request=request,
                payload={"certificate_uid": certificate.certificate_uid},
            )

        return Response(ProgressEntrySerializer(entry).data)


@extend_schema(
    tags=["Progress"],
    responses={200: EnrollmentProgressSerializer},
    description="Gets overall progress for one of the current user's own enrollments: percent "
    "complete per lesson, and an aggregate overall_percent.",
    examples=[
        OpenApiExample(
            "Progress",
            value={
                "enrollment_id": "d4e5f6a7-...",
                "status": "active",
                "overall_percent": 40,
                "lessons": [
                    {
                        "lesson_id": "d1e2f3a4-...",
                        "lesson_title": "Welcome",
                        "percent_complete": 75,
                        "last_position_seconds": 420,
                        "last_viewed_at": "2026-01-16T11:00:00Z",
                    }
                ],
            },
            response_only=True,
        )
    ],
)
class ProgressDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, enrollment_id):
        enrollment = get_object_or_404(Enrollment, pk=enrollment_id)
        if enrollment.student_id != request.user.id:
            raise PermissionDenied("Not your enrollment.")

        entries = enrollment.progress_entries.select_related("lesson").all()
        total_lessons = Lesson.objects.filter(section__course_id=enrollment.course_id).count()
        overall = 0
        if total_lessons:
            overall = sum(e.percent_complete for e in entries) // total_lessons

        return Response(
            EnrollmentProgressSerializer(
                {
                    "enrollment_id": enrollment.id,
                    "status": enrollment.status,
                    "overall_percent": min(overall, 100),
                    "lessons": entries,
                }
            ).data
        )


@extend_schema(
    tags=["Student"],
    description="Adds a timestamped free-text note on a lesson within a course the current "
    "user is enrolled in.",
    examples=[
        OpenApiExample(
            "Create note",
            value={
                "lesson_id": "d1e2f3a4-...",
                "note_text": "Remember: list comprehensions vs generator expressions.",
                "timestamp_seconds": 210,
            },
            request_only=True,
        )
    ],
)
class LessonNoteCreateView(generics.CreateAPIView):
    serializer_class = LessonNoteCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        lesson = get_object_or_404(Lesson, pk=serializer.validated_data["lesson_id"])
        _enrollment_for_lesson_or_404(self.request.user, lesson)
        serializer.save(student=self.request.user, lesson=lesson)


@extend_schema(
    tags=["Student"],
    description="Adds a timestamped bookmark on a lesson within a course the current user is "
    "enrolled in.",
    examples=[
        OpenApiExample(
            "Create bookmark",
            value={"lesson_id": "d1e2f3a4-...", "timestamp_seconds": 210, "label": "Key example"},
            request_only=True,
        )
    ],
)
class BookmarkCreateView(generics.CreateAPIView):
    serializer_class = BookmarkCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        lesson = get_object_or_404(Lesson, pk=serializer.validated_data["lesson_id"])
        _enrollment_for_lesson_or_404(self.request.user, lesson)
        serializer.save(student=self.request.user, lesson=lesson)


_CERTIFICATE_EXAMPLE = {
    "id": "f1e2d3c4-...",
    "certificate_uid": "CERT-2026-0001",
    "course": {
        "id": "1c2d3e4f-...",
        "title": "Complete Python Bootcamp",
        "slug": "complete-python-bootcamp",
        "summary": "Learn Python from scratch, from syntax to real projects.",
    },
    "qr_payload": "https://skillchain.example.com/verify/CERT-2026-0001",
    "pdf_key": "certificates/CERT-2026-0001.pdf",
    "issued_at": "2026-01-20T09:00:00Z",
}


@extend_schema(
    tags=["Certificates"],
    description="Lists certificates issued to the current user, most recently issued first.",
    examples=[OpenApiExample("Certificate", value=_CERTIFICATE_EXAMPLE, response_only=True)],
)
class CertificateListView(generics.ListAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = IssuedAtCursorPagination

    def get_queryset(self):
        return Certificate.objects.filter(
            enrollment__student=self.request.user
        ).select_related("enrollment__course", "enrollment__student__profile")

    def list(self, request, *args, **kwargs):
        # Self-heals certificates issued before pdf_file existed (or whose
        # render previously failed) — cheap since it's a no-op once a
        # certificate already has a file.
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        for certificate in page if page is not None else queryset:
            ensure_certificate_pdf(certificate)

        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


@extend_schema(
    tags=["Certificates"],
    responses={200: CertificateVerifyResponseSerializer},
    description="Public, unauthenticated lookup verifying whether a certificate UID (e.g. from "
    "a QR code) is genuine.",
    examples=[
        OpenApiExample(
            "Valid",
            value={
                "valid": True,
                "certificate_uid": "CERT-2026-0001",
                "course_title": "Complete Python Bootcamp",
                "student_email": "student@example.com",
                "issued_at": "2026-01-20T09:00:00Z",
            },
            response_only=True,
        ),
        OpenApiExample("Not found", value={"valid": False}, response_only=True),
    ],
)
class CertificateVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, certificate_uid):
        certificate = (
            Certificate.objects.select_related("enrollment__course", "enrollment__student")
            .filter(certificate_uid=certificate_uid)
            .first()
        )
        if certificate is None:
            return Response({"valid": False}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            CertificateVerifyResponseSerializer(
                {
                    "valid": True,
                    "certificate_uid": certificate.certificate_uid,
                    "course_title": certificate.enrollment.course.title,
                    "student_email": certificate.enrollment.student.email,
                    "issued_at": certificate.issued_at,
                }
            ).data
        )
