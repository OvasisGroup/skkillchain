from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audit.services import record_event
from apps.catalog.models import Course
from shared.api.pagination import SortOrderCursorPagination

from .models import Lesson, Section
from .serializers import LessonWriteSerializer, SectionWriteSerializer


def _owned_course_or_403(course_id, user):
    course = get_object_or_404(Course, pk=course_id)
    if course.owner_id != user.id:
        raise PermissionDenied("You do not own this course.")
    return course


def _editable_or_400(course):
    # Instructors can keep adding curriculum after launch (new lectures on a
    # published course is the normal case) — only blocked mid-review
    # (submitted/approved, so a moderator isn't reviewing content that then
    # changes under them) or once archived.
    allowed = (Course.STATUS_DRAFT, Course.STATUS_REJECTED, Course.STATUS_PUBLISHED)
    if course.status not in allowed:
        raise ValidationError(
            f"Cannot edit content while the course is '{course.status}'; "
            "only draft, rejected, or published courses can be edited."
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Instructor"],
        description="Lists sections for a course the current instructor owns.",
        examples=[
            OpenApiExample(
                "Section",
                value={"id": "c1d2e3f4-...", "title": "Getting Started", "sort_order": 1},
                response_only=True,
            )
        ],
    ),
    post=extend_schema(
        tags=["Instructor"],
        description="Creates a section within a course the current instructor owns. Only "
        "allowed while the course is draft or rejected.",
        examples=[
            OpenApiExample(
                "Create section",
                value={"title": "Getting Started", "sort_order": 1},
                request_only=True,
            )
        ],
    ),
)
class InstructorSectionCreateView(generics.ListCreateAPIView):
    serializer_class = SectionWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SortOrderCursorPagination

    def get_queryset(self):
        _owned_course_or_403(self.kwargs["course_id"], self.request.user)
        return Section.objects.filter(course_id=self.kwargs["course_id"])

    def perform_create(self, serializer):
        course = _owned_course_or_403(self.kwargs["course_id"], self.request.user)
        _editable_or_400(course)
        section = serializer.save(course=course)
        record_event(
            actor=self.request.user,
            action="section.create",
            entity_type="Section",
            entity_id=section.id,
            request=self.request,
            payload={"course_id": str(course.id)},
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Instructor"],
        description="Lists lessons within a section belonging to a course the current "
        "instructor owns.",
        examples=[
            OpenApiExample(
                "Lesson",
                value={
                    "id": "d1e2f3a4-...",
                    "title": "Welcome",
                    "lesson_type": "video",
                    "sort_order": 1,
                    "duration_seconds": 180,
                    "is_preview": True,
                },
                response_only=True,
            )
        ],
    ),
    post=extend_schema(
        tags=["Instructor"],
        description="Creates a lesson within a section belonging to a course the current "
        "instructor owns. Only allowed while the course is draft or rejected.",
        examples=[
            OpenApiExample(
                "Create lesson",
                value={
                    "title": "Welcome",
                    "lesson_type": "video",
                    "sort_order": 1,
                    "duration_seconds": 180,
                    "is_preview": True,
                },
                request_only=True,
            )
        ],
    ),
)
class InstructorLessonCreateView(generics.ListCreateAPIView):
    serializer_class = LessonWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SortOrderCursorPagination

    def get_queryset(self):
        section = get_object_or_404(Section, pk=self.kwargs["section_id"])
        _owned_course_or_403(section.course_id, self.request.user)
        return Lesson.objects.filter(section_id=self.kwargs["section_id"])

    def perform_create(self, serializer):
        section = get_object_or_404(Section, pk=self.kwargs["section_id"])
        course = _owned_course_or_403(section.course_id, self.request.user)
        _editable_or_400(course)
        lesson = serializer.save(section=section)
        record_event(
            actor=self.request.user,
            action="lesson.create",
            entity_type="Lesson",
            entity_id=lesson.id,
            request=self.request,
            payload={"section_id": str(section.id)},
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Instructor"],
        description="Retrieves a lesson within a course the current instructor owns.",
    ),
    patch=extend_schema(
        tags=["Instructor"],
        description="Updates a lesson the current instructor owns — including attaching or "
        "replacing its content_file (video/PDF upload). Only allowed while the course is "
        "draft or rejected.",
    ),
)
class InstructorLessonDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = LessonWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Lesson.objects.all()
    lookup_url_kwarg = "id"

    def get_object(self):
        lesson = get_object_or_404(Lesson.objects.select_related("section"), pk=self.kwargs["id"])
        _owned_course_or_403(lesson.section.course_id, self.request.user)
        return lesson

    def perform_update(self, serializer):
        lesson = self.get_object()
        course = _owned_course_or_403(lesson.section.course_id, self.request.user)
        _editable_or_400(course)
        updated = serializer.save()
        record_event(
            actor=self.request.user,
            action="lesson.update",
            entity_type="Lesson",
            entity_id=updated.id,
            request=self.request,
        )
