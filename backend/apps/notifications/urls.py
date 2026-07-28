from django.urls import path

from . import views

urlpatterns = [
    path("notifications/", views.NotificationListView.as_view(), name="notification-list"),
    path(
        "notifications/mark-read/",
        views.NotificationMarkReadView.as_view(),
        name="notification-mark-read",
    ),
]
