from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.audit.services import record_event

from . import services
from .models import Message, Thread
from .serializers import (
    MessageCreateSerializer,
    MessageSerializer,
    ThreadCreateSerializer,
    ThreadSerializer,
)


def _participant_thread_or_403(user, thread_id) -> Thread:
    thread = get_object_or_404(Thread, id=thread_id)
    if not thread.participants.filter(user=user).exists():
        raise PermissionDenied("You are not a participant of this thread.")
    return thread


_THREAD_EXAMPLE = {
    "id": "a1b2c3d4-...",
    "thread_type": "direct",
    "subject": "",
    "created_by": "b6a5b6c0-...",
    "created_at": "2026-02-01T12:00:00Z",
    "participant_ids": ["b6a5b6c0-...", "c7b6c7d1-..."],
}


@extend_schema_view(
    get=extend_schema(
        tags=["Messaging"],
        description="Lists message threads the current user participates in.",
        examples=[OpenApiExample("Thread", value=_THREAD_EXAMPLE, response_only=True)],
    ),
    post=extend_schema(
        tags=["Messaging"],
        description="Starts a new message thread with the given participants. Also used for "
        "the WebSocket-backed real-time channel — see docs/07-delivery-planning M7 for the "
        "WS auth handshake.",
        examples=[
            OpenApiExample(
                "Create thread",
                value={
                    "thread_type": "direct",
                    "participant_ids": ["c7b6c7d1-5e6f-7a8b-9c0d-1e2f3a4b5c6d"],
                },
                request_only=True,
            ),
            OpenApiExample("Created", value=_THREAD_EXAMPLE, response_only=True),
        ],
    ),
)
class ThreadListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return ThreadCreateSerializer if self.request.method == "POST" else ThreadSerializer

    def get_queryset(self):
        return Thread.objects.filter(participants__user=self.request.user).distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        thread = services.create_thread(
            request.user,
            participant_ids=serializer.validated_data["participant_ids"],
            thread_type=serializer.validated_data["thread_type"],
            subject=serializer.validated_data["subject"],
        )
        record_event(
            actor=request.user,
            action="thread.create",
            entity_type="Thread",
            entity_id=thread.id,
            request=request,
        )
        return Response(ThreadSerializer(thread).data, status=201)


@extend_schema_view(
    get=extend_schema(
        tags=["Messaging"],
        description="Lists messages in a thread the current user participates in.",
        examples=[
            OpenApiExample(
                "Message",
                value={
                    "id": "d4e5f6a7-...",
                    "thread": "a1b2c3d4-...",
                    "sender": "b6a5b6c0-...",
                    "body": "Hi! Quick question about lesson 3.",
                    "metadata": {},
                    "created_at": "2026-02-01T12:05:00Z",
                },
                response_only=True,
            )
        ],
    ),
    post=extend_schema(
        tags=["Messaging"],
        description="Sends a message in a thread the current user participates in. Also "
        "broadcast over the thread's WebSocket channel to connected participants in real time.",
        examples=[
            OpenApiExample(
                "Send message",
                value={"body": "Hi! Quick question about lesson 3."},
                request_only=True,
            )
        ],
    ),
)
class ThreadMessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return MessageCreateSerializer if self.request.method == "POST" else MessageSerializer

    def get_queryset(self):
        thread = _participant_thread_or_403(self.request.user, self.kwargs["thread_id"])
        return Message.objects.filter(thread=thread).select_related("sender")

    def create(self, request, *args, **kwargs):
        thread = _participant_thread_or_403(request.user, self.kwargs["thread_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = services.create_message(thread, request.user, serializer.validated_data["body"])
        record_event(
            actor=request.user,
            action="message.send",
            entity_type="Message",
            entity_id=message.id,
            request=request,
        )
        return Response(MessageSerializer(message).data, status=201)
