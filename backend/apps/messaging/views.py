from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
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


@extend_schema(tags=["Messaging"])
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


@extend_schema(tags=["Messaging"])
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
