from django.urls import path

from . import views

urlpatterns = [
    path("analytics/revenue/", views.RevenueReportView.as_view(), name="analytics-revenue"),
    path(
        "analytics/course-performance/",
        views.CoursePerformanceReportView.as_view(),
        name="analytics-course-performance",
    ),
    path(
        "analytics/student-engagement/",
        views.StudentEngagementReportView.as_view(),
        name="analytics-student-engagement",
    ),
    path(
        "analytics/completion/", views.CompletionReportView.as_view(), name="analytics-completion"
    ),
    path("analytics/watch-time/", views.WatchTimeReportView.as_view(), name="analytics-watch-time"),
    path("analytics/drop-off/", views.DropOffReportView.as_view(), name="analytics-drop-off"),
    path(
        "analytics/instructor-earnings/",
        views.InstructorEarningsReportView.as_view(),
        name="analytics-instructor-earnings",
    ),
    # M9's admin-report aliases — same views, same permissions, no
    # duplicated logic for the same underlying data (see the milestone
    # doc's own overlap between §11 Admin APIs and §12 Analytics APIs).
    path("admin/reports/revenue/", views.RevenueReportView.as_view(), name="admin-report-revenue"),
    path(
        "admin/reports/engagement/",
        views.StudentEngagementReportView.as_view(),
        name="admin-report-engagement",
    ),
]
