from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.authorization.permissions import HasPermission
from apps.content.serializers import SectionSerializer

from .models import Category, Course, InvalidCourseTransition, Tag
from .serializers import (
    CategorySerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    CoursePreviewSectionSerializer,
    CourseRejectSerializer,
    CourseWriteSerializer,
    TagSerializer,
)


def _owned_course_or_403(course_id, user):
    course = get_object_or_404(Course, pk=course_id)
    if course.owner_id != user.id:
        raise PermissionDenied("You do not own this course.")
    return course


# ---------- Public catalog browsing ----------


@extend_schema(tags=["Courses"])
class CourseListView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Course.objects.filter(status=Course.STATUS_PUBLISHED)
        params = self.request.query_params
        if category := params.get("category"):
            qs = qs.filter(categories__slug=category)
        if language := params.get("language"):
            qs = qs.filter(language=language)
        if difficulty := params.get("difficulty"):
            qs = qs.filter(difficulty=difficulty)
        return qs.distinct()


@extend_schema(tags=["Courses"])
class CourseDetailView(generics.RetrieveAPIView):
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"

    def get_queryset(self):
        return Course.objects.all()

    def get_object(self):
        course = super().get_object()
        user = self.request.user
        is_owner = user.is_authenticated and course.owner_id == user.id
        if course.status != Course.STATUS_PUBLISHED and not is_owner:
            # Same response as "doesn't exist" — an unpublished course's
            # existence isn't information a non-owner should get either.
            raise Http404
        return course


@extend_schema(tags=["Courses"], responses={200: CoursePreviewSectionSerializer(many=True)})
class CoursePreviewView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        course = get_object_or_404(Course, pk=id, status=Course.STATUS_PUBLISHED)
        sections = course.sections.prefetch_related("lessons").all()
        preview_only = []
        for section in sections:
            preview_lessons = [lesson for lesson in section.lessons.all() if lesson.is_preview]
            if preview_lessons:
                preview_only.append({"section": section, "lessons": preview_lessons})
        data = [
            {
                "section": SectionSerializer(entry["section"]).data["title"],
                "lessons": [
                    {
                        "id": str(lesson.id),
                        "title": lesson.title,
                        "duration_seconds": lesson.duration_seconds,
                    }
                    for lesson in entry["lessons"]
                ],
            }
            for entry in preview_only
        ]
        return Response(data)


@extend_schema(tags=["Courses"])
class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    queryset = Category.objects.all()
    pagination_class = None


@extend_schema(tags=["Courses"])
class TagListView(generics.ListAPIView):
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Tag.objects.all()
    pagination_class = None


# ---------- Instructor authoring ----------


@extend_schema(tags=["Instructor"])
class InstructorCourseListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return CourseWriteSerializer if self.request.method == "POST" else CourseListSerializer

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        course = serializer.save()
        record_event(
            actor=self.request.user,
            action="course.create",
            entity_type="Course",
            entity_id=course.id,
            request=self.request,
        )


@extend_schema(tags=["Instructor"])
class InstructorCourseDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = CourseWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user)

    def perform_update(self, serializer):
        course = self.get_object()
        if course.status not in (Course.STATUS_DRAFT, Course.STATUS_REJECTED):
            raise ValidationError(
                f"Cannot edit a course while it is '{course.status}'; only draft or rejected courses can be edited."
            )
        serializer.save()


@extend_schema(tags=["Instructor"], request=None, responses={200: CourseDetailSerializer})
class CourseSubmitReviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        course = _owned_course_or_403(id, request.user)
        try:
            course.submit_for_review()
        except InvalidCourseTransition as exc:
            raise ValidationError(str(exc)) from exc
        record_event(
            actor=request.user,
            action="course.submit_review",
            entity_type="Course",
            entity_id=course.id,
            request=request,
        )
        return Response(CourseDetailSerializer(course).data)


@extend_schema(tags=["Instructor"], request=None, responses={200: CourseDetailSerializer})
class CoursePublishView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        course = _owned_course_or_403(id, request.user)
        try:
            course.publish()
        except InvalidCourseTransition as exc:
            raise ValidationError(str(exc)) from exc
        record_event(
            actor=request.user,
            action="course.publish",
            entity_type="Course",
            entity_id=course.id,
            request=request,
        )
        return Response(CourseDetailSerializer(course).data)


# ---------- Review / moderation (permission-gated, not ownership-gated) ----------


@extend_schema(tags=["Admin"])
class CoursesPendingReviewView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [HasPermission]
    required_permission = "courses.approve"
    queryset = Course.objects.filter(status=Course.STATUS_SUBMITTED)


@extend_schema(tags=["Admin"], request=None, responses={200: CourseDetailSerializer})
class CourseApproveView(APIView):
    permission_classes = [HasPermission]
    required_permission = "courses.approve"
    throttle_scope = "admin-write"

    def post(self, request, id):
        course = get_object_or_404(Course, pk=id)
        try:
            course.approve()
        except InvalidCourseTransition as exc:
            raise ValidationError(str(exc)) from exc
        record_event(
            actor=request.user,
            action="course.approve",
            entity_type="Course",
            entity_id=course.id,
            request=request,
        )
        return Response(CourseDetailSerializer(course).data)


@extend_schema(
    tags=["Admin"], request=CourseRejectSerializer, responses={200: CourseDetailSerializer}
)
class CourseRejectView(APIView):
    permission_classes = [HasPermission]
    required_permission = "courses.approve"
    throttle_scope = "admin-write"

    def post(self, request, id):
        serializer = CourseRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course = get_object_or_404(Course, pk=id)
        try:
            course.reject(serializer.validated_data["reason"])
        except InvalidCourseTransition as exc:
            raise ValidationError(str(exc)) from exc
        record_event(
            actor=request.user,
            action="course.reject",
            entity_type="Course",
            entity_id=course.id,
            request=request,
            payload={"reason": serializer.validated_data["reason"]},
        )
        return Response(CourseDetailSerializer(course).data)
