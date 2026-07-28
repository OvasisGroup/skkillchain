from django.urls import path

from . import views

urlpatterns = [
    path(
        "privacy/erasure-requests/",
        views.DataErasureRequestCreateView.as_view(),
        name="privacy-erasure-request-create",
    ),
    path(
        "admin/privacy/erasure-requests/",
        views.AdminErasureRequestListView.as_view(),
        name="admin-privacy-erasure-request-list",
    ),
    path(
        "admin/privacy/legal-holds/<uuid:user_id>/",
        views.AdminLegalHoldCreateView.as_view(),
        name="admin-privacy-legal-hold-create",
    ),
    path(
        "admin/privacy/legal-holds/<uuid:hold_id>/release/",
        views.AdminLegalHoldReleaseView.as_view(),
        name="admin-privacy-legal-hold-release",
    ),
]
