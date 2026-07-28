from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.catalog.models import Course
from shared.api.pagination import StartedAtCursorPagination

from . import services
from .anthropic_client import AIProviderError
from .models import AiChatMessage, AiChatSession
from .serializers import (
    AiChatMessageCreateSerializer,
    AiChatMessageSerializer,
    AiChatSessionCreateSerializer,
    AiChatSessionSerializer,
)


def _own_session_or_403(user, session_id) -> AiChatSession:
    session = get_object_or_404(AiChatSession, id=session_id)
    if session.user_id != user.id:
        raise PermissionDenied("You can only access your own tutor sessions.")
    return session


@extend_schema(tags=["AI"])
class AiTutorSessionCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StartedAtCursorPagination

    def get_serializer_class(self):
        return AiChatSessionCreateSerializer if self.request.method == "POST" else AiChatSessionSerializer

    def get_queryset(self):
        return AiChatSession.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = get_object_or_404(Course, id=serializer.validated_data["course_id"])
        session = services.create_chat_session(request.user, course)
        return Response(AiChatSessionSerializer(session).data, status=201)


@extend_schema(tags=["AI"])
class AiTutorMessageCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "ai-chat"

    def get_serializer_class(self):
        return (
            AiChatMessageCreateSerializer if self.request.method == "POST" else AiChatMessageSerializer
        )

    def get_queryset(self):
        session = _own_session_or_403(self.request.user, self.kwargs["session_id"])
        return AiChatMessage.objects.filter(session=session)

    def create(self, request, *args, **kwargs):
        session = _own_session_or_403(request.user, self.kwargs["session_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            reply = services.send_chat_message(session, request.user, serializer.validated_data["body"])
        except AIProviderError as exc:
            raise ValidationError(f"AI tutor request failed: {exc}") from exc
        return Response(AiChatMessageSerializer(reply).data, status=201)
