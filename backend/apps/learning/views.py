from django.db.models import Max
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.services import record_analytics_event
from apps.audit.services import record_event
from apps.catalog.models import Course
from apps.content.models import Lesson
from shared.api.pagination import EnrolledAtCursorPagination, IssuedAtCursorPagination

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
    EnrollmentProgressSerializer,
    EnrollmentSerializer,
    EnrollRequestSerializer,
    LessonNoteCreateSerializer,
    ProgressEntrySerializer,
    ProgressUpdateSerializer,
    WishlistItemSerializer,
)
from .services import maybe_complete_enrollment


def _enrollment_for_lesson_or_404(user, lesson):
    enrollment = Enrollment.objects.filter(student=user, course_id=lesson.section.course_id).first()
    if enrollment is None:
        raise PermissionDenied("You must be enrolled in this course.")
    return enrollment


@extend_schema(
    tags=["Student"], request=EnrollRequestSerializer, responses={201: EnrollmentSerializer}
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


@extend_schema(tags=["Student"])
class MyCoursesView(generics.ListAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = EnrolledAtCursorPagination

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user).select_related("course")


@extend_schema(tags=["Student"])
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


@extend_schema(tags=["Student"])
class WishlistView(generics.ListAPIView):
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist.items.select_related("course")


class WishlistItemAddRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["Student"], request=None, responses={201: None, 200: None})
    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id, status=Course.STATUS_PUBLISHED)
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        _, created = WishlistItem.objects.get_or_create(wishlist=wishlist, course=course)
        return Response(status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @extend_schema(tags=["Student"], responses={204: None})
    def delete(self, request, course_id):
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        deleted, _ = WishlistItem.objects.filter(wishlist=wishlist, course_id=course_id).delete()
        if not deleted:
            raise NotFound("Not in your wishlist.")
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Progress"], request=ProgressUpdateSerializer, responses={200: ProgressEntrySerializer}
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


@extend_schema(tags=["Progress"], responses={200: EnrollmentProgressSerializer})
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


@extend_schema(tags=["Student"])
class LessonNoteCreateView(generics.CreateAPIView):
    serializer_class = LessonNoteCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        lesson = get_object_or_404(Lesson, pk=serializer.validated_data["lesson_id"])
        _enrollment_for_lesson_or_404(self.request.user, lesson)
        serializer.save(student=self.request.user, lesson=lesson)


@extend_schema(tags=["Student"])
class BookmarkCreateView(generics.CreateAPIView):
    serializer_class = BookmarkCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        lesson = get_object_or_404(Lesson, pk=serializer.validated_data["lesson_id"])
        _enrollment_for_lesson_or_404(self.request.user, lesson)
        serializer.save(student=self.request.user, lesson=lesson)


@extend_schema(tags=["Certificates"])
class CertificateListView(generics.ListAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = IssuedAtCursorPagination

    def get_queryset(self):
        return Certificate.objects.filter(enrollment__student=self.request.user).select_related(
            "enrollment__course"
        )


@extend_schema(tags=["Certificates"], responses={200: CertificateVerifyResponseSerializer})
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
