from django.urls import path

from . import views

urlpatterns = [
    # Public / student
    path("hackathons/", views.HackathonListView.as_view(), name="hackathon-list"),
    path("hackathons/<uuid:id>/", views.HackathonDetailView.as_view(), name="hackathon-detail"),
    path(
        "hackathons/<uuid:id>/register/",
        views.HackathonRegisterView.as_view(),
        name="hackathon-register",
    ),
    path(
        "hackathons/<uuid:id>/submission/",
        views.HackathonSubmissionView.as_view(),
        name="hackathon-submission",
    ),
    path(
        "students/me/hackathons/",
        views.MyHackathonRegistrationsView.as_view(),
        name="my-hackathon-registrations",
    ),
    # Organizer
    path(
        "organizer/hackathons/",
        views.OrganizerHackathonListCreateView.as_view(),
        name="organizer-hackathon-list-create",
    ),
    path(
        "organizer/hackathons/<uuid:id>/",
        views.OrganizerHackathonDetailView.as_view(),
        name="organizer-hackathon-detail",
    ),
    path(
        "organizer/hackathons/<uuid:id>/publish/",
        views.HackathonPublishView.as_view(),
        name="hackathon-publish",
    ),
    path(
        "organizer/hackathons/<uuid:id>/cancel/",
        views.HackathonCancelView.as_view(),
        name="hackathon-cancel",
    ),
    path(
        "organizer/hackathons/<uuid:id>/registrations/",
        views.OrganizerHackathonRegistrationsView.as_view(),
        name="organizer-hackathon-registrations",
    ),
    path(
        "organizer/hackathons/<uuid:id>/winners/",
        views.HackathonWinnerCreateView.as_view(),
        name="hackathon-winner-create",
    ),
    # Moderation
    path("admin/hackathons/", views.AdminHackathonListView.as_view(), name="hackathon-admin-list"),
    path(
        "admin/hackathons/<uuid:id>/",
        views.AdminHackathonDetailView.as_view(),
        name="hackathon-admin-detail",
    ),
    path(
        "admin/hackathons/<uuid:id>/cancel/",
        views.HackathonAdminCancelView.as_view(),
        name="hackathon-admin-cancel",
    ),
    path(
        "admin/hackathons/<uuid:id>/registrations/",
        views.AdminHackathonRegistrationsView.as_view(),
        name="hackathon-admin-registrations",
    ),
    path(
        "admin/hackathons/<uuid:id>/winners/",
        views.AdminHackathonWinnerCreateView.as_view(),
        name="hackathon-admin-winner-create",
    ),
    path(
        "admin/hackathons/<uuid:id>/gallery-images/",
        views.AdminHackathonGalleryImageListCreateView.as_view(),
        name="hackathon-admin-gallery-image-list-create",
    ),
    path(
        "admin/hackathons/<uuid:id>/gallery-images/<uuid:image_id>/",
        views.AdminHackathonGalleryImageDetailView.as_view(),
        name="hackathon-admin-gallery-image-detail",
    ),
]
