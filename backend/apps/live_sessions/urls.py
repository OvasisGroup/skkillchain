from django.urls import path

from . import views

urlpatterns = [
    path(
        "instructor/conferencing-accounts/<str:provider>/connect/",
        views.ConferencingAccountConnectView.as_view(),
        name="conferencing-account-connect",
    ),
    path(
        "instructor/conferencing-accounts/<str:provider>/callback/",
        views.ConferencingAccountCallbackView.as_view(),
        name="conferencing-account-callback",
    ),
    path(
        "instructor/conferencing-accounts/",
        views.ConferencingAccountListView.as_view(),
        name="conferencing-account-list",
    ),
    path(
        "instructor/conferencing-accounts/<uuid:account_id>/",
        views.ConferencingAccountRevokeView.as_view(),
        name="conferencing-account-revoke",
    ),
    path(
        "instructor/courses/<uuid:course_id>/live-sessions/",
        views.LiveSessionScheduleView.as_view(),
        name="live-session-schedule",
    ),
    path(
        "instructor/live-sessions/<uuid:id>/",
        views.LiveSessionUpdateView.as_view(),
        name="live-session-update",
    ),
    path(
        "instructor/live-sessions/<uuid:id>/cancel/",
        views.LiveSessionCancelView.as_view(),
        name="live-session-cancel",
    ),
    path(
        "instructor/live-sessions/<uuid:id>/registrations/",
        views.LiveSessionRegistrationsView.as_view(),
        name="live-session-registrations",
    ),
    path(
        "courses/<uuid:course_id>/live-sessions/",
        views.CourseLiveSessionsView.as_view(),
        name="course-live-sessions",
    ),
    path("students/me/live-sessions/", views.MyLiveSessionsView.as_view(), name="my-live-sessions"),
    path(
        "live-sessions/<uuid:id>/register/",
        views.LiveSessionRegisterView.as_view(),
        name="live-session-register",
    ),
    path(
        "live-sessions/<uuid:id>/join/",
        views.LiveSessionJoinView.as_view(),
        name="live-session-join",
    ),
    path(
        "live-sessions/<uuid:id>/recording/",
        views.LiveSessionRecordingView.as_view(),
        name="live-session-recording",
    ),
]
