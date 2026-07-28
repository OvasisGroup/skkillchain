from rest_framework import serializers

from .models import (
    CourseCompletionAggregate,
    EngagementDailyAggregate,
    InstructorEarningsAggregate,
    LessonDropOffAggregate,
    LessonWatchTimeAggregate,
    RevenueDailyAggregate,
)


class RevenueDailyAggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenueDailyAggregate
        fields = ["period_start", "period_end", "currency", "gross_amount", "net_amount"]


class EngagementDailyAggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngagementDailyAggregate
        fields = [
            "course",
            "period_start",
            "period_end",
            "active_students_count",
            "new_enrollments_count",
        ]


class CourseCompletionAggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCompletionAggregate
        fields = [
            "course",
            "period_start",
            "period_end",
            "enrollments_count",
            "completions_count",
            "completion_rate",
        ]


class LessonWatchTimeAggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonWatchTimeAggregate
        fields = ["lesson", "period_start", "period_end", "total_watch_seconds", "views_count"]


class LessonDropOffAggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonDropOffAggregate
        fields = [
            "lesson",
            "period_start",
            "period_end",
            "started_count",
            "completed_count",
            "drop_off_rate",
        ]


class InstructorEarningsAggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorEarningsAggregate
        fields = ["period_start", "period_end", "currency", "gross_amount", "net_amount"]


class CoursePerformanceSerializer(serializers.Serializer):
    completion = CourseCompletionAggregateSerializer(allow_null=True)
    engagement = EngagementDailyAggregateSerializer(allow_null=True)
