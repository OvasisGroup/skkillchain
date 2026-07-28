from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authorization.permissions import HasPermission

from .models import (
    CourseCompletionAggregate,
    EngagementDailyAggregate,
    InstructorEarningsAggregate,
    LessonDropOffAggregate,
    LessonWatchTimeAggregate,
    RevenueDailyAggregate,
)
from .serializers import (
    CourseCompletionAggregateSerializer,
    CoursePerformanceSerializer,
    EngagementDailyAggregateSerializer,
    InstructorEarningsAggregateSerializer,
    LessonDropOffAggregateSerializer,
    LessonWatchTimeAggregateSerializer,
    RevenueDailyAggregateSerializer,
)


@extend_schema(
    tags=["Analytics"],
    description="Lists daily platform revenue aggregates. Also mounted at "
    "GET /admin/reports/revenue — same view, same permission, no duplicated logic for the "
    "same underlying data.",
    examples=[
        OpenApiExample(
            "Revenue day",
            value={
                "period_start": "2026-02-01T00:00:00Z",
                "period_end": "2026-02-02T00:00:00Z",
                "currency": "USD",
                "gross_amount": "5230.00",
                "net_amount": "4707.00",
            },
            response_only=True,
        )
    ],
)
class RevenueReportView(generics.ListAPIView):
    """Also mounted at GET /admin/reports/revenue (see
    apps.analytics.urls) — same view, same permission, no duplicated
    logic for the same underlying data."""

    serializer_class = RevenueDailyAggregateSerializer
    permission_classes = [HasPermission]
    required_permission = "reports.view_revenue"
    pagination_class = None
    queryset = RevenueDailyAggregate.objects.all()


@extend_schema(
    tags=["Analytics"],
    parameters=[OpenApiParameter("course_id", str, description="Filter to a single course.")],
    description="Lists daily student-engagement aggregates, optionally filtered to one "
    "course. Also mounted at GET /admin/reports/engagement.",
    examples=[
        OpenApiExample(
            "Engagement day",
            value={
                "course": "1c2d3e4f-...",
                "period_start": "2026-02-01T00:00:00Z",
                "period_end": "2026-02-02T00:00:00Z",
                "active_students_count": 120,
                "new_enrollments_count": 8,
            },
            response_only=True,
        )
    ],
)
class StudentEngagementReportView(generics.ListAPIView):
    """Also mounted at GET /admin/reports/engagement (see
    apps.analytics.urls)."""

    serializer_class = EngagementDailyAggregateSerializer
    permission_classes = [HasPermission]
    required_permission = "reports.view"
    pagination_class = None

    def get_queryset(self):
        queryset = EngagementDailyAggregate.objects.all()
        course_id = self.request.query_params.get("course_id")
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset


@extend_schema(
    tags=["Analytics"],
    parameters=[OpenApiParameter("course_id", str, description="Filter to a single course.")],
    description="Lists course completion-rate aggregates, optionally filtered to one course.",
    examples=[
        OpenApiExample(
            "Completion",
            value={
                "course": "1c2d3e4f-...",
                "period_start": "2026-02-01T00:00:00Z",
                "period_end": "2026-02-02T00:00:00Z",
                "enrollments_count": 500,
                "completions_count": 210,
                "completion_rate": "0.42",
            },
            response_only=True,
        )
    ],
)
class CompletionReportView(generics.ListAPIView):
    serializer_class = CourseCompletionAggregateSerializer
    permission_classes = [HasPermission]
    required_permission = "reports.view"
    pagination_class = None

    def get_queryset(self):
        queryset = CourseCompletionAggregate.objects.all()
        course_id = self.request.query_params.get("course_id")
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset


@extend_schema(
    tags=["Analytics"],
    parameters=[OpenApiParameter("lesson_id", str, description="Filter to a single lesson.")],
    description="Lists per-lesson total watch-time aggregates, optionally filtered to one "
    "lesson.",
    examples=[
        OpenApiExample(
            "Watch time",
            value={
                "lesson": "d1e2f3a4-...",
                "period_start": "2026-02-01T00:00:00Z",
                "period_end": "2026-02-02T00:00:00Z",
                "total_watch_seconds": 48000,
                "views_count": 320,
            },
            response_only=True,
        )
    ],
)
class WatchTimeReportView(generics.ListAPIView):
    serializer_class = LessonWatchTimeAggregateSerializer
    permission_classes = [HasPermission]
    required_permission = "reports.view"
    pagination_class = None

    def get_queryset(self):
        queryset = LessonWatchTimeAggregate.objects.all()
        lesson_id = self.request.query_params.get("lesson_id")
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        return queryset


@extend_schema(
    tags=["Analytics"],
    parameters=[OpenApiParameter("lesson_id", str, description="Filter to a single lesson.")],
    description="Lists per-lesson drop-off aggregates (started vs. completed viewers), "
    "optionally filtered to one lesson.",
    examples=[
        OpenApiExample(
            "Drop-off",
            value={
                "lesson": "d1e2f3a4-...",
                "period_start": "2026-02-01T00:00:00Z",
                "period_end": "2026-02-02T00:00:00Z",
                "started_count": 300,
                "completed_count": 180,
                "drop_off_rate": "0.40",
            },
            response_only=True,
        )
    ],
)
class DropOffReportView(generics.ListAPIView):
    serializer_class = LessonDropOffAggregateSerializer
    permission_classes = [HasPermission]
    required_permission = "reports.view"
    pagination_class = None

    def get_queryset(self):
        queryset = LessonDropOffAggregate.objects.all()
        lesson_id = self.request.query_params.get("lesson_id")
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        return queryset


@extend_schema(tags=["Analytics"])
class CoursePerformanceReportView(APIView):
    """Combines the latest completion + engagement snapshot for one
    course — a single course_id query param is required since
    "performance" here means one course's current standing, not a
    platform-wide list."""

    permission_classes = [HasPermission]
    required_permission = "reports.view"

    @extend_schema(
        responses={200: CoursePerformanceSerializer},
        parameters=[
            OpenApiParameter("course_id", str, required=True, description="Course to report on.")
        ],
        description="Combines the latest completion and engagement snapshot for one course. "
        "Either field is null if no aggregate has been computed yet for that course.",
        examples=[
            OpenApiExample(
                "Performance",
                value={
                    "completion": {
                        "course": "1c2d3e4f-...",
                        "period_start": "2026-02-01T00:00:00Z",
                        "period_end": "2026-02-02T00:00:00Z",
                        "enrollments_count": 500,
                        "completions_count": 210,
                        "completion_rate": "0.42",
                    },
                    "engagement": {
                        "course": "1c2d3e4f-...",
                        "period_start": "2026-02-01T00:00:00Z",
                        "period_end": "2026-02-02T00:00:00Z",
                        "active_students_count": 120,
                        "new_enrollments_count": 8,
                    },
                },
                response_only=True,
            )
        ],
    )
    def get(self, request):
        course_id = request.query_params.get("course_id")
        if not course_id:
            raise ValidationError({"course_id": "This query parameter is required."})

        completion = CourseCompletionAggregate.objects.filter(course_id=course_id).first()
        engagement = EngagementDailyAggregate.objects.filter(course_id=course_id).first()
        return Response(
            {
                "completion": (
                    CourseCompletionAggregateSerializer(completion).data if completion else None
                ),
                "engagement": (
                    EngagementDailyAggregateSerializer(engagement).data if engagement else None
                ),
            }
        )


@extend_schema(
    tags=["Analytics"],
    description="Lists the current instructor's own earnings aggregates. There is no "
    "instructor_id parameter — it always scopes to the authenticated user, so this can only "
    "ever return the caller's own numbers by construction, not by a permission check that "
    "could be gotten wrong.",
    examples=[
        OpenApiExample(
            "Earnings",
            value={
                "period_start": "2026-02-01T00:00:00Z",
                "period_end": "2026-02-02T00:00:00Z",
                "currency": "USD",
                "gross_amount": "1200.00",
                "net_amount": "1080.00",
            },
            response_only=True,
        )
    ],
)
class InstructorEarningsReportView(generics.ListAPIView):
    """No instructor_id parameter exists on this endpoint at all — it
    always scopes to request.user, so "an instructor's earnings report
    can only ever return that instructor's own numbers, even if they
    pass another instructor's ID" holds by construction, not by a
    permission check that could be gotten wrong."""

    serializer_class = InstructorEarningsAggregateSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return InstructorEarningsAggregate.objects.filter(instructor=self.request.user)
