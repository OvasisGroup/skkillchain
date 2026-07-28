from drf_spectacular.utils import extend_schema
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


@extend_schema(tags=["Analytics"])
class RevenueReportView(generics.ListAPIView):
    """Also mounted at GET /admin/reports/revenue (see
    apps.analytics.urls) — same view, same permission, no duplicated
    logic for the same underlying data."""

    serializer_class = RevenueDailyAggregateSerializer
    permission_classes = [HasPermission]
    required_permission = "reports.view_revenue"
    pagination_class = None
    queryset = RevenueDailyAggregate.objects.all()


@extend_schema(tags=["Analytics"])
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


@extend_schema(tags=["Analytics"])
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


@extend_schema(tags=["Analytics"])
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


@extend_schema(tags=["Analytics"])
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

    @extend_schema(responses={200: CoursePerformanceSerializer})
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


@extend_schema(tags=["Analytics"])
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
