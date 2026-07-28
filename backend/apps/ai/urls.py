from django.urls import path

from . import views

urlpatterns = [
    path(
        "ai/tutor/sessions/",
        views.AiTutorSessionCreateView.as_view(),
        name="ai-tutor-session-list-create",
    ),
    path(
        "ai/tutor/sessions/<uuid:session_id>/messages/",
        views.AiTutorMessageCreateView.as_view(),
        name="ai-tutor-message-list-create",
    ),
]
