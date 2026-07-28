from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.audit.services import record_event

from . import services
from .models import SupportTicket, SupportTicketMessage
from .serializers import (
    SupportTicketCreateSerializer,
    SupportTicketMessageCreateSerializer,
    SupportTicketMessageSerializer,
    SupportTicketSerializer,
)


def _party_ticket_or_403(user, ticket_id) -> SupportTicket:
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    if user.id not in (ticket.requester_id, ticket.assignee_id):
        raise PermissionDenied("You are not a party to this support ticket.")
    return ticket


@extend_schema(tags=["Support"])
class SupportTicketListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return (
            SupportTicketCreateSerializer
            if self.request.method == "POST"
            else SupportTicketSerializer
        )

    def get_queryset(self):
        user = self.request.user
        return SupportTicket.objects.filter(Q(requester=user) | Q(assignee=user)).distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = services.create_ticket(
            request.user,
            category=serializer.validated_data["category"],
            priority=serializer.validated_data["priority"],
            subject=serializer.validated_data["subject"],
            body=serializer.validated_data["body"],
        )
        record_event(
            actor=request.user,
            action="support_ticket.create",
            entity_type="SupportTicket",
            entity_id=ticket.id,
            request=request,
        )
        return Response(SupportTicketSerializer(ticket).data, status=201)


@extend_schema(tags=["Support"])
class SupportTicketMessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return (
            SupportTicketMessageCreateSerializer
            if self.request.method == "POST"
            else SupportTicketMessageSerializer
        )

    def get_queryset(self):
        ticket = _party_ticket_or_403(self.request.user, self.kwargs["ticket_id"])
        return SupportTicketMessage.objects.filter(ticket=ticket).select_related("sender")

    def create(self, request, *args, **kwargs):
        ticket = _party_ticket_or_403(request.user, self.kwargs["ticket_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = services.add_ticket_message(ticket, request.user, serializer.validated_data["body"])
        record_event(
            actor=request.user,
            action="support_ticket.reply",
            entity_type="SupportTicketMessage",
            entity_id=message.id,
            request=request,
        )
        return Response(SupportTicketMessageSerializer(message).data, status=201)
