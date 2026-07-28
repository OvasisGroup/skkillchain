from django.urls import path

from . import views

urlpatterns = [
    path("notifications/", views.NotificationListView.as_view(), name="notification-list"),
    path(
        "notifications/mark-read/",
        views.NotificationMarkReadView.as_view(),
        name="notification-mark-read",
    ),
    path(
        "admin/notification-templates/",
        views.AdminNotificationTemplateListView.as_view(),
        name="admin-notification-template-list",
    ),
    path(
        "admin/notification-templates/<str:code>/",
        views.AdminNotificationTemplateUpdateView.as_view(),
        name="admin-notification-template-update",
    ),
    path(
        "admin/email-templates/",
        views.AdminEmailTemplateListView.as_view(),
        name="admin-email-template-list",
    ),
    path(
        "admin/email-templates/<str:code>/",
        views.AdminEmailTemplateUpdateView.as_view(),
        name="admin-email-template-update",
    ),
]
