from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.audit.services import record_event
from apps.authorization.permissions import HasPermission

from . import services
from .models import SupportTicket, SupportTicketMessage
from .serializers import (
    AdminSupportTicketUpdateSerializer,
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


_SUPPORT_TICKET_EXAMPLE = {
    "id": "d0e1f2a3-...",
    "requester": "b6a5b6c0-...",
    "assignee": None,
    "category": "billing",
    "priority": "normal",
    "status": "open",
    "subject": "Refund not received",
    "is_sla_breached": False,
    "created_at": "2026-02-01T14:00:00Z",
    "updated_at": "2026-02-01T14:00:00Z",
}


@extend_schema_view(
    get=extend_schema(
        tags=["Support"],
        description="Lists support tickets the current user is a party to (requester or "
        "assignee).",
        examples=[OpenApiExample("Ticket", value=_SUPPORT_TICKET_EXAMPLE, response_only=True)],
    ),
    post=extend_schema(
        tags=["Support"],
        description="Opens a new support ticket.",
        examples=[
            OpenApiExample(
                "Open ticket",
                value={
                    "category": "billing",
                    "priority": "normal",
                    "subject": "Refund not received",
                    "body": "I requested a refund 5 days ago and haven't seen it yet.",
                },
                request_only=True,
            ),
            OpenApiExample("Created", value=_SUPPORT_TICKET_EXAMPLE, response_only=True),
        ],
    ),
)
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


@extend_schema_view(
    get=extend_schema(
        tags=["Support"],
        description="Lists messages on a support ticket the current user is a party to.",
        examples=[
            OpenApiExample(
                "Message",
                value={
                    "id": "e1f2a3b4-...",
                    "ticket": "d0e1f2a3-...",
                    "sender": "b6a5b6c0-...",
                    "body": "Any update on this?",
                    "created_at": "2026-02-02T09:00:00Z",
                },
                response_only=True,
            )
        ],
    ),
    post=extend_schema(
        tags=["Support"],
        description="Posts a message on a support ticket the current user is a party to.",
        examples=[
            OpenApiExample("Reply", value={"body": "Any update on this?"}, request_only=True)
        ],
    ),
)
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
        message = services.add_ticket_message(
            ticket, request.user, serializer.validated_data["body"]
        )
        record_event(
            actor=request.user,
            action="support_ticket.reply",
            entity_type="SupportTicketMessage",
            entity_id=message.id,
            request=request,
        )
        return Response(SupportTicketMessageSerializer(message).data, status=201)


@extend_schema(
    tags=["Admin"],
    description="Lists all support tickets across all requesters.",
    examples=[OpenApiExample("Ticket", value=_SUPPORT_TICKET_EXAMPLE, response_only=True)],
)
class AdminSupportTicketListView(generics.ListAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [HasPermission]
    required_permission = "support_tickets.manage"
    queryset = SupportTicket.objects.all()
    pagination_class = None


@extend_schema(
    tags=["Admin"],
    request=AdminSupportTicketUpdateSerializer,
    responses={200: SupportTicketSerializer},
    description="Assigns and/or updates the status/priority of a support ticket.",
    examples=[
        OpenApiExample(
            "Assign and resolve",
            value={"assignee": "c7b6c7d1-...", "status": "resolved"},
            request_only=True,
        ),
        OpenApiExample(
            "Updated",
            value={
                **_SUPPORT_TICKET_EXAMPLE,
                "assignee": "c7b6c7d1-...",
                "status": "resolved",
            },
            response_only=True,
        ),
    ],
)
class AdminSupportTicketUpdateView(generics.UpdateAPIView):
    serializer_class = AdminSupportTicketUpdateSerializer
    permission_classes = [HasPermission]
    required_permission = "support_tickets.manage"
    throttle_scope = "admin-write"
    queryset = SupportTicket.objects.all()

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        ticket = self.get_object()
        return Response(SupportTicketSerializer(ticket).data)
