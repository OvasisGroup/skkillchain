from django.urls import path

from . import admin_views

urlpatterns = [
    path("admin/users/", admin_views.AdminUserListView.as_view(), name="admin-user-list"),
    path(
        "admin/users/<uuid:user_id>/status/",
        admin_views.AdminUserStatusUpdateView.as_view(),
        name="admin-user-status-update",
    ),
    path(
        "admin/users/<uuid:user_id>/profile/",
        admin_views.AdminUserProfileView.as_view(),
        name="admin-user-profile",
    ),
    path(
        "admin/users/<uuid:user_id>/avatar/",
        admin_views.AdminUserAvatarUploadView.as_view(),
        name="admin-user-avatar",
    ),
]
