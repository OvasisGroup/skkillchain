from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
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


_COURSE_LIST_EXAMPLE = {
    "id": "1c2d3e4f-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
    "title": "Complete Python Bootcamp",
    "slug": "complete-python-bootcamp",
    "summary": "Learn Python from scratch, from syntax to real projects.",
    "instructor": {"id": "b6a5b6c0-9b1e-4c9a-9b7a-1f2e3d4c5b6a", "email": "jane@example.com"},
    "price_amount": "49.99",
    "currency": "USD",
    "language": "en",
    "difficulty": "beginner",
    "status": "published",
    "published_at": "2026-01-10T12:00:00Z",
}

# ---------- Public catalog browsing ----------


@extend_schema(
    tags=["Courses"],
    parameters=[
        OpenApiParameter("category", str, description="Filter by category slug."),
        OpenApiParameter("language", str, description="Filter by ISO language code, e.g. en."),
        OpenApiParameter(
            "difficulty", str, description="Filter by difficulty: beginner/intermediate/advanced."
        ),
    ],
    description="Lists published courses, optionally filtered by category, language, "
    "and/or difficulty.",
    examples=[OpenApiExample("Course", value=_COURSE_LIST_EXAMPLE, response_only=True)],
)
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


@extend_schema(
    tags=["Courses"],
    description="Gets a published course's full detail. The owning instructor can also see "
    "their own unpublished (draft/submitted/rejected) course through this same endpoint; "
    "anyone else gets a 404, identical to a nonexistent course.",
    examples=[
        OpenApiExample(
            "Course detail",
            value={
                **_COURSE_LIST_EXAMPLE,
                "description": "A full walkthrough of Python fundamentals and projects.",
                "rejection_reason": "",
                "categories": [{"id": "e1f2...", "name": "Programming", "slug": "programming"}],
                "tags": [{"id": "a1b2...", "name": "Python", "slug": "python"}],
                "prerequisites": ["Basic computer literacy"],
                "learning_objectives": ["Write and run Python scripts", "Use core data types"],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-10T12:00:00Z",
            },
            response_only=True,
        )
    ],
)
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


@extend_schema(
    tags=["Courses"],
    responses={200: CoursePreviewSectionSerializer(many=True)},
    description="Returns only the sections/lessons an instructor has marked as free preview "
    "content, for a published course — used on a course's public landing page before "
    "enrollment.",
    examples=[
        OpenApiExample(
            "Preview",
            value=[
                {
                    "section": "Getting Started",
                    "lessons": [
                        {"id": "a1b2c3d4-...", "title": "Welcome", "duration_seconds": 180}
                    ],
                }
            ],
            response_only=True,
        )
    ],
)
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


@extend_schema(
    tags=["Courses"],
    description="Lists all course categories, for use as the 'category' filter on GET /courses.",
    examples=[
        OpenApiExample(
            "Category",
            value={"id": "e1f2a3b4-...", "name": "Programming", "slug": "programming"},
            response_only=True,
        )
    ],
)
class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    queryset = Category.objects.all()
    pagination_class = None


@extend_schema(
    tags=["Courses"],
    description="Lists all course tags.",
    examples=[
        OpenApiExample(
            "Tag",
            value={"id": "a1b2c3d4-...", "name": "Python", "slug": "python"},
            response_only=True,
        )
    ],
)
class TagListView(generics.ListAPIView):
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Tag.objects.all()
    pagination_class = None


# ---------- Instructor authoring ----------

_COURSE_WRITE_EXAMPLE = {
    "title": "Complete Python Bootcamp",
    "summary": "Learn Python from scratch, from syntax to real projects.",
    "description": "A full walkthrough of Python fundamentals and projects.",
    "language": "en",
    "difficulty": "beginner",
    "price_amount": "49.99",
    "currency": "USD",
}


@extend_schema_view(
    get=extend_schema(
        tags=["Instructor"],
        description="Lists the current instructor's own courses, at any status "
        "(draft/submitted/approved/published/rejected).",
        examples=[OpenApiExample("Course", value=_COURSE_LIST_EXAMPLE, response_only=True)],
    ),
    post=extend_schema(
        tags=["Instructor"],
        description="Creates a new course as a draft, owned by the current instructor.",
        examples=[
            OpenApiExample("Create course", value=_COURSE_WRITE_EXAMPLE, request_only=True),
            OpenApiExample(
                "Created", value={**_COURSE_WRITE_EXAMPLE, "status": "draft"}, response_only=True
            ),
        ],
    ),
)
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


@extend_schema_view(
    get=extend_schema(
        tags=["Instructor"],
        description="Gets one of the current instructor's own courses (any status).",
        examples=[
            OpenApiExample(
                "Course", value={**_COURSE_WRITE_EXAMPLE, "status": "draft"}, response_only=True
            )
        ],
    ),
    patch=extend_schema(
        tags=["Instructor"],
        description="Partially updates a draft or rejected course. Submitted/approved/"
        "published courses can't be edited directly — see POST .../submit-review.",
        examples=[
            OpenApiExample(
                "Update summary", value={"summary": "Updated summary"}, request_only=True
            )
        ],
    ),
    put=extend_schema(
        tags=["Instructor"],
        description="Replaces a draft or rejected course's fields.",
        examples=[OpenApiExample("Replace course", value=_COURSE_WRITE_EXAMPLE, request_only=True)],
    ),
)
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


@extend_schema(
    tags=["Instructor"],
    request=None,
    responses={200: CourseDetailSerializer},
    description="Submits a draft course for content review (draft/rejected -> submitted). "
    "Fails with 400 if the course isn't in a state that can be submitted.",
    examples=[
        OpenApiExample(
            "Submitted", value={**_COURSE_WRITE_EXAMPLE, "status": "submitted"}, response_only=True
        )
    ],
)
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


@extend_schema(
    tags=["Instructor"],
    request=None,
    responses={200: CourseDetailSerializer},
    description="Publishes an approved course (approved -> published), making it visible on "
    "the public catalog. Fails with 400 if the course hasn't been approved yet.",
    examples=[
        OpenApiExample(
            "Published", value={**_COURSE_WRITE_EXAMPLE, "status": "published"}, response_only=True
        )
    ],
)
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


@extend_schema(
    tags=["Admin"],
    description="Lists courses awaiting content review (status=submitted). Requires the "
    "courses.approve permission.",
    examples=[
        OpenApiExample(
            "Course", value={**_COURSE_LIST_EXAMPLE, "status": "submitted"}, response_only=True
        )
    ],
)
class CoursesPendingReviewView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [HasPermission]
    required_permission = "courses.approve"
    queryset = Course.objects.filter(status=Course.STATUS_SUBMITTED)


@extend_schema(
    tags=["Admin"],
    request=None,
    responses={200: CourseDetailSerializer},
    description="Approves a submitted course (submitted -> approved). Requires the "
    "courses.approve permission.",
    examples=[
        OpenApiExample(
            "Approved", value={**_COURSE_WRITE_EXAMPLE, "status": "approved"}, response_only=True
        )
    ],
)
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
    tags=["Admin"],
    request=CourseRejectSerializer,
    responses={200: CourseDetailSerializer},
    description="Rejects a submitted course with a reason (submitted -> rejected). The "
    "instructor can then edit and resubmit. Requires the courses.approve permission.",
    examples=[
        OpenApiExample(
            "Reject",
            value={"reason": "Missing closed captions on video lessons."},
            request_only=True,
        ),
        OpenApiExample(
            "Rejected",
            value={
                **_COURSE_WRITE_EXAMPLE,
                "status": "rejected",
                "rejection_reason": "Missing closed captions on video lessons.",
            },
            response_only=True,
        ),
    ],
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
