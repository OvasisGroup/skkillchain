from django.contrib import admin

from .models import (
    AnalyticsEvent,
    CourseCompletionAggregate,
    EngagementDailyAggregate,
    InstructorEarningsAggregate,
    LessonDropOffAggregate,
    LessonWatchTimeAggregate,
    RevenueDailyAggregate,
)


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ["event_name", "actor", "course", "occurred_at"]
    list_filter = ["event_name"]


@admin.register(RevenueDailyAggregate)
class RevenueDailyAggregateAdmin(admin.ModelAdmin):
    list_display = ["period_start", "period_end", "currency", "gross_amount", "net_amount"]


@admin.register(EngagementDailyAggregate)
class EngagementDailyAggregateAdmin(admin.ModelAdmin):
    list_display = ["course", "period_start", "active_students_count", "new_enrollments_count"]


@admin.register(CourseCompletionAggregate)
class CourseCompletionAggregateAdmin(admin.ModelAdmin):
    list_display = [
        "course",
        "period_start",
        "enrollments_count",
        "completions_count",
        "completion_rate",
    ]


@admin.register(LessonWatchTimeAggregate)
class LessonWatchTimeAggregateAdmin(admin.ModelAdmin):
    list_display = ["lesson", "period_start", "total_watch_seconds", "views_count"]


@admin.register(LessonDropOffAggregate)
class LessonDropOffAggregateAdmin(admin.ModelAdmin):
    list_display = ["lesson", "period_start", "started_count", "completed_count", "drop_off_rate"]


@admin.register(InstructorEarningsAggregate)
class InstructorEarningsAggregateAdmin(admin.ModelAdmin):
    list_display = ["instructor", "period_start", "period_end", "gross_amount", "net_amount"]
