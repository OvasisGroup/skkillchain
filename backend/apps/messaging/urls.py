from django.urls import path

from . import views

urlpatterns = [
    path("threads/", views.ThreadListCreateView.as_view(), name="thread-list-create"),
    path(
        "threads/<uuid:thread_id>/messages/",
        views.ThreadMessageListCreateView.as_view(),
        name="thread-message-list-create",
    ),
]
