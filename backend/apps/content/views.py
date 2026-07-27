from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audit.services import record_event
from apps.catalog.models import Course

from .models import Lesson, Section
from .serializers import LessonWriteSerializer, SectionWriteSerializer


def _owned_course_or_403(course_id, user):
    course = get_object_or_404(Course, pk=course_id)
    if course.owner_id != user.id:
        raise PermissionDenied("You do not own this course.")
    return course


def _editable_or_400(course):
    if course.status not in (Course.STATUS_DRAFT, Course.STATUS_REJECTED):
        raise ValidationError(
            f"Cannot edit content while the course is '{course.status}'; "
            "only draft or rejected courses can be edited."
        )


@extend_schema(tags=["Instructor"])
class InstructorSectionCreateView(generics.ListCreateAPIView):
    serializer_class = SectionWriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
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


@extend_schema(tags=["Instructor"])
class InstructorLessonCreateView(generics.ListCreateAPIView):
    serializer_class = LessonWriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
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
