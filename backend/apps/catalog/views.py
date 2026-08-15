from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch, Q
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
    AdminCourseWriteSerializer,
    CategorySerializer,
    CategoryWriteSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    CourseNotifySerializer,
    CoursePreviewSectionSerializer,
    CourseRejectSerializer,
    CourseWriteSerializer,
    InstructorDetailSerializer,
    InstructorListSerializer,
    TagSerializer,
    TagWriteSerializer,
)

User = get_user_model()


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
        OpenApiParameter("q", str, description="Case-insensitive search over title and summary."),
        OpenApiParameter(
            "is_free", bool, description="If true, only free courses; if false, only paid ones."
        ),
    ],
    description="Lists published courses, optionally filtered by category, language, "
    "difficulty, a free-text search, and/or price.",
    examples=[OpenApiExample("Course", value=_COURSE_LIST_EXAMPLE, response_only=True)],
)
class CourseListView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Course.objects.filter(status=Course.STATUS_PUBLISHED).select_related(
            "owner", "owner__profile"
        )
        params = self.request.query_params
        if category := params.get("category"):
            qs = qs.filter(category__slug=category)
        if language := params.get("language"):
            qs = qs.filter(language=language)
        if difficulty := params.get("difficulty"):
            qs = qs.filter(difficulty=difficulty)
        if q := params.get("q"):
            qs = qs.filter(Q(title__icontains=q) | Q(summary__icontains=q))
        if (is_free := params.get("is_free")) is not None:
            qs = (
                qs.filter(price_amount=0)
                if is_free.lower() in ("true", "1")
                else qs.exclude(price_amount=0)
            )
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
                "category": {"id": "e1f2...", "name": "Programming", "slug": "programming"},
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
        return Course.objects.select_related(
            "owner", "owner__profile", "category"
        ).prefetch_related("tags", "prerequisites", "learning_objectives")

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


@extend_schema_view(
    get=extend_schema(
        tags=["Courses"],
        description="Lists all course categories, for use as the 'category' filter on "
        "GET /courses and as the required category picker when authoring a course.",
        examples=[
            OpenApiExample(
                "Category",
                value={"id": "e1f2a3b4-...", "name": "Programming", "slug": "programming"},
                response_only=True,
            )
        ],
    ),
    post=extend_schema(
        tags=["Admin"],
        description="Creates a new category. Requires the categories.manage permission — "
        "categories are a curated taxonomy, unlike tags which any authenticated user can add.",
        examples=[
            OpenApiExample("Create", value={"name": "Programming"}, request_only=True),
        ],
    ),
)
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    pagination_class = None

    def get_serializer_class(self):
        return CategoryWriteSerializer if self.request.method == "POST" else CategorySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [HasPermission()]
        return [permissions.AllowAny()]

    required_permission = "categories.manage"


@extend_schema_view(
    get=extend_schema(tags=["Courses"], description="Gets a single category."),
    patch=extend_schema(
        tags=["Admin"],
        description="Partially updates a category. Requires the categories.manage permission.",
    ),
    put=extend_schema(
        tags=["Admin"],
        description="Replaces a category. Requires the categories.manage permission.",
    ),
    delete=extend_schema(
        tags=["Admin"],
        description="Deletes a category. Requires the categories.manage permission. Fails "
        "with 400 if any course still references it (courses always belong to exactly one "
        "category, so deletion is blocked rather than silently orphaning them).",
    ),
)
class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    lookup_field = "id"

    def get_serializer_class(self):
        return CategorySerializer if self.request.method == "GET" else CategoryWriteSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [HasPermission()]

    required_permission = "categories.manage"

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.courses.exists():
            raise ValidationError(
                "Cannot delete a category that is still assigned to one or more courses."
            )
        return super().destroy(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        tags=["Courses"],
        description="Lists all course tags.",
        examples=[
            OpenApiExample(
                "Tag",
                value={"id": "a1b2c3d4-...", "name": "Python", "slug": "python"},
                response_only=True,
            )
        ],
    ),
    post=extend_schema(
        tags=["Courses"],
        description="Creates a tag, or returns the existing one if a tag with the same name "
        "(case-insensitive) already exists — any authenticated user can add tags inline while "
        "authoring a course, so this is idempotent rather than erroring on a duplicate name.",
        examples=[OpenApiExample("Create", value={"name": "Python"}, request_only=True)],
    ),
)
class TagListCreateView(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def post(self, request, *args, **kwargs):
        name = (request.data.get("name") or "").strip()
        if not name:
            raise ValidationError({"name": ["This field is required."]})

        tag = Tag.objects.filter(name__iexact=name).first()
        if tag is not None:
            return Response(TagSerializer(tag).data)

        tag = Tag.objects.create(name=name)
        return Response(TagSerializer(tag).data, status=201)


@extend_schema_view(
    get=extend_schema(tags=["Courses"], description="Gets a single tag."),
    patch=extend_schema(
        tags=["Admin"],
        description="Partially updates a tag. Requires the tags.manage permission.",
    ),
    put=extend_schema(
        tags=["Admin"],
        description="Replaces a tag. Requires the tags.manage permission.",
    ),
    delete=extend_schema(
        tags=["Admin"],
        description="Deletes a tag. Requires the tags.manage permission.",
    ),
)
class TagDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    lookup_field = "id"

    def get_serializer_class(self):
        return TagSerializer if self.request.method == "GET" else TagWriteSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [HasPermission()]

    required_permission = "tags.manage"


def _instructor_queryset():
    # An "instructor" here means "has at least one published course" —
    # the platform's instructor role is granted on application approval
    # (apps.moderation.services.approve_instructor_application) before
    # they've necessarily published anything, so role membership alone
    # would surface empty profiles on a public directory. Annotated count
    # is scoped to published courses too, so it always matches what
    # get_courses() on InstructorDetailSerializer actually lists.
    # Prefetched onto `_published_courses` so InstructorListSerializer.get_categories()
    # and InstructorDetailSerializer.get_courses() can read from it in Python
    # instead of each issuing its own query per instructor (see catalog/serializers.py).
    published_courses = Prefetch(
        "owned_courses",
        queryset=Course.objects.filter(status=Course.STATUS_PUBLISHED).select_related("category"),
        to_attr="_published_courses",
    )
    return (
        User.objects.filter(owned_courses__status=Course.STATUS_PUBLISHED)
        .select_related("profile")
        .prefetch_related(published_courses)
        .annotate(
            published_course_count=Count(
                "owned_courses",
                filter=Q(owned_courses__status=Course.STATUS_PUBLISHED),
                distinct=True,
            )
        )
        .distinct()
        .order_by("-created_at", "email")
    )


@extend_schema(
    tags=["Courses"],
    description="Lists every instructor with at least one published course, newest "
    "instructor first — the public instructor directory.",
    examples=[
        OpenApiExample(
            "Instructor",
            value={
                "id": "b6a5b6c0-9b1e-4c9a-9b7a-1f2e3d4c5b6a",
                "email": "jane@example.com",
                "profile": {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "bio": "Backend engineer and educator.",
                    "avatar": None,
                    "linkedin_url": "",
                    "twitter_url": "",
                    "github_url": "",
                    "youtube_url": "",
                    "website_url": "",
                },
                "published_course_count": 3,
                "categories": [{"id": "e1f2...", "name": "Programming", "slug": "programming"}],
            },
            response_only=True,
        )
    ],
)
class InstructorListView(generics.ListAPIView):
    serializer_class = InstructorListSerializer
    permission_classes = [permissions.AllowAny]
    queryset = _instructor_queryset()
    # Deliberately unpaginated (tests/api/test_catalog.py::TestInstructorDirectory
    # asserts a flat list) — the directory is scoped to users with at least one
    # published course, which keeps it far smaller than the full user table.
    # If this grows large enough to matter, paginating it is a frontend-visible
    # API change, not just a backend one.
    pagination_class = None


@extend_schema(
    tags=["Courses"],
    description="Gets one instructor's public profile plus every course they've published. "
    "404s for a user with no published courses, same as a nonexistent instructor.",
)
class InstructorDetailView(generics.RetrieveAPIView):
    serializer_class = InstructorDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"

    def get_queryset(self):
        return _instructor_queryset()


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
        return Course.objects.filter(owner=self.request.user).select_related(
            "owner", "owner__profile"
        )

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
        description="Partially updates a draft, rejected, or published course. Editing a "
        "published course notifies every enrolled student. Submitted/approved courses can't "
        "be edited directly (mid-review) — see POST .../submit-review.",
        examples=[
            OpenApiExample(
                "Update summary", value={"summary": "Updated summary"}, request_only=True
            )
        ],
    ),
    put=extend_schema(
        tags=["Instructor"],
        description="Replaces a draft, rejected, or published course's fields. Editing a "
        "published course notifies every enrolled student.",
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
        # Blocked only mid-review (submitted/approved, so a moderator isn't
        # reviewing content that then changes under them) or once archived —
        # same allowance as content.views._editable_or_400 for section/lesson
        # edits, so a published course's title/price/etc. can be kept in
        # sync with its curriculum without unpublishing first.
        allowed = (Course.STATUS_DRAFT, Course.STATUS_REJECTED, Course.STATUS_PUBLISHED)
        if course.status not in allowed:
            raise ValidationError(
                f"Cannot edit a course while it is '{course.status}'; only draft, rejected, "
                "or published courses can be edited."
            )
        serializer.save()
        if course.status == Course.STATUS_PUBLISHED:
            from .tasks import notify_course_update

            notify_course_update.delay(str(course.id))


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
    queryset = Course.objects.filter(status=Course.STATUS_SUBMITTED).select_related(
        "owner", "owner__profile"
    )


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


# ---------- Admin course management (courses.manage permission) ----------
# Distinct from the review/moderation views above (courses.approve): those
# gate the submitted->approved/rejected workflow only. These give full CRUD
# over every course regardless of owner or status, plus the ability to
# create a course on an instructor's behalf and message a course's
# instructor/students directly — administrator/super_administrator only,
# see catalog/migrations/0007_seed_course_manage_permission.py.


@extend_schema_view(
    get=extend_schema(
        tags=["Admin"],
        parameters=[
            OpenApiParameter("status", str, description="Filter by course status."),
            OpenApiParameter("category", str, description="Filter by category slug."),
            OpenApiParameter("language", str, description="Filter by ISO language code."),
            OpenApiParameter(
                "difficulty",
                str,
                description="Filter by difficulty: beginner/intermediate/advanced.",
            ),
            OpenApiParameter(
                "q", str, description="Case-insensitive search over title and summary."
            ),
        ],
        description="Lists every course platform-wide, any owner or status. Requires the "
        "courses.manage permission.",
        examples=[OpenApiExample("Course", value=_COURSE_LIST_EXAMPLE, response_only=True)],
    ),
    post=extend_schema(
        tags=["Admin"],
        description="Creates a new draft course on behalf of the instructor given by "
        "owner_id. Requires the courses.manage permission.",
        examples=[
            OpenApiExample(
                "Create for instructor",
                value={**_COURSE_WRITE_EXAMPLE, "owner_id": "b6a5b6c0-9b1e-4c9a-9b7a-1f2e3d4c5b6a"},
                request_only=True,
            ),
            OpenApiExample(
                "Created", value={**_COURSE_WRITE_EXAMPLE, "status": "draft"}, response_only=True
            ),
        ],
    ),
)
class AdminCourseListView(generics.ListCreateAPIView):
    permission_classes = [HasPermission]
    required_permission = "courses.manage"

    def get_serializer_class(self):
        return AdminCourseWriteSerializer if self.request.method == "POST" else CourseListSerializer

    def get_queryset(self):
        qs = Course.objects.all().select_related("owner", "owner__profile", "category")
        params = self.request.query_params
        if status := params.get("status"):
            qs = qs.filter(status=status)
        if category := params.get("category"):
            qs = qs.filter(category__slug=category)
        if language := params.get("language"):
            qs = qs.filter(language=language)
        if difficulty := params.get("difficulty"):
            qs = qs.filter(difficulty=difficulty)
        if q := params.get("q"):
            qs = qs.filter(Q(title__icontains=q) | Q(summary__icontains=q))
        return qs.distinct()

    def perform_create(self, serializer):
        course = serializer.save()
        record_event(
            actor=self.request.user,
            action="course.create",
            entity_type="Course",
            entity_id=course.id,
            request=self.request,
            payload={"owner_id": str(course.owner_id), "created_by": "admin"},
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Admin"],
        description="Gets any course by id, any owner or status. Requires the "
        "courses.manage permission.",
        examples=[
            OpenApiExample(
                "Course", value={**_COURSE_WRITE_EXAMPLE, "status": "draft"}, response_only=True
            )
        ],
    ),
    patch=extend_schema(
        tags=["Admin"],
        description="Partially updates any course's record (title/summary/description/"
        "price/category/tags/cover/prerequisites/objectives) regardless of owner or "
        "status. Curriculum (sections/lessons/quizzes) isn't editable here — that stays "
        "instructor-only. Editing a published course notifies every enrolled student, "
        "same as the instructor-facing edit. Requires the courses.manage permission.",
        examples=[
            OpenApiExample(
                "Update summary", value={"summary": "Updated summary"}, request_only=True
            )
        ],
    ),
    put=extend_schema(
        tags=["Admin"],
        description="Replaces any course's record fields. Requires the courses.manage "
        "permission.",
        examples=[OpenApiExample("Replace course", value=_COURSE_WRITE_EXAMPLE, request_only=True)],
    ),
)
class AdminCourseDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [HasPermission]
    required_permission = "courses.manage"
    lookup_url_kwarg = "id"
    queryset = Course.objects.select_related(
        "owner", "owner__profile", "category"
    ).prefetch_related("tags", "prerequisites", "learning_objectives")

    def get_serializer_class(self):
        # CourseWriteSerializer's prerequisites/learning_objectives are
        # write_only (see its Meta comment) and category_id/tag_ids are
        # bare ids — fine for a PATCH/PUT body, but a GET through the same
        # serializer would silently omit prerequisites/objectives, which
        # would then read as "clear them" on the next save since the admin
        # edit form always resubmits every field. CourseDetailSerializer's
        # full read shape avoids that trap.
        return (
            CourseDetailSerializer if self.request.method == "GET" else AdminCourseWriteSerializer
        )

    def perform_update(self, serializer):
        course = self.get_object()
        serializer.save()
        if course.status == Course.STATUS_PUBLISHED:
            from .tasks import notify_course_update

            notify_course_update.delay(str(course.id))


@extend_schema(
    tags=["Admin"],
    request=CourseNotifySerializer,
    responses={200: CourseNotifySerializer},
    description="Sends a message to a course's instructor and/or its enrolled students, "
    "always over both in-app and email channels. Requires the courses.manage permission.",
    examples=[
        OpenApiExample(
            "Notify both",
            value={
                "audience": "both",
                "subject": "Heads up about your course",
                "message": "We've made a small update to the catalog listing rules.",
            },
            request_only=True,
        )
    ],
)
class AdminCourseNotifyView(APIView):
    permission_classes = [HasPermission]
    required_permission = "courses.manage"
    throttle_scope = "admin-write"

    def post(self, request, id):
        course = get_object_or_404(Course, pk=id)
        serializer = CourseNotifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        audience = serializer.validated_data["audience"]
        subject = serializer.validated_data["subject"]
        message = serializer.validated_data["message"]

        if audience in (
            CourseNotifySerializer.AUDIENCE_INSTRUCTOR,
            CourseNotifySerializer.AUDIENCE_BOTH,
        ):
            from apps.notifications.services import notify

            notify(
                course.owner,
                type="course_update",
                channels=["in_app", "email"],
                title=subject,
                body=message,
            )
        if audience in (
            CourseNotifySerializer.AUDIENCE_STUDENTS,
            CourseNotifySerializer.AUDIENCE_BOTH,
        ):
            from .tasks import notify_course_recipients

            notify_course_recipients.delay(str(course.id), subject, message)

        record_event(
            actor=request.user,
            action="course.notify",
            entity_type="Course",
            entity_id=course.id,
            request=request,
            payload={"audience": audience, "subject": subject},
        )
        return Response(serializer.validated_data)
