from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.authorization.permissions import HasPermission
from shared.api.pagination import RequestedAtCursorPagination

from . import services
from .models import DataErasureRequest
from .serializers import (
    DataErasureRequestSerializer,
    LegalHoldCreateSerializer,
    LegalHoldSerializer,
)

_ERASURE_REQUEST_EXAMPLE = {
    "id": "a1b2c3d4-...",
    "user": "b6a5b6c0-...",
    "user_email": "erased-user-b6a5b6c0.../erased.invalid",
    "status": "completed",
    "block_reason": "",
    "requested_at": "2026-02-01T09:00:00Z",
    "completed_at": "2026-02-01T09:00:01Z",
}


@extend_schema(
    tags=["Privacy"],
    request=None,
    responses={201: DataErasureRequestSerializer},
    description="Requests erasure of the current user's personal data (GDPR/CCPA right to be "
    "forgotten). Anonymizes email/profile and deletes OAuth identities/MFA factors, but keeps "
    "the account row itself since Order/Payment records PROTECT-FK to it. If an active legal "
    "hold exists on the account, the request is recorded as blocked instead of executed.",
    examples=[
        OpenApiExample("Completed", value=_ERASURE_REQUEST_EXAMPLE, response_only=True),
        OpenApiExample(
            "Blocked",
            value={
                **_ERASURE_REQUEST_EXAMPLE,
                "status": "blocked",
                "block_reason": "Open chargeback dispute",
                "completed_at": None,
            },
            response_only=True,
        ),
    ],
)
class DataErasureRequestCreateView(APIView):
    """Self-service GDPR/CCPA right-to-erasure request for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        erasure_request = services.request_erasure(request.user)
        record_event(
            actor=request.user,
            action="data_erasure_request.create",
            entity_type="DataErasureRequest",
            entity_id=erasure_request.id,
            request=request,
            payload={"status": erasure_request.status},
        )
        return Response(DataErasureRequestSerializer(erasure_request).data, status=201)


@extend_schema(
    tags=["Admin"],
    description="Lists all data erasure requests, for compliance oversight.",
    examples=[
        OpenApiExample("Erasure request", value=_ERASURE_REQUEST_EXAMPLE, response_only=True)
    ],
)
class AdminErasureRequestListView(generics.ListAPIView):
    serializer_class = DataErasureRequestSerializer
    permission_classes = [HasPermission]
    required_permission = "privacy.manage"
    pagination_class = RequestedAtCursorPagination
    queryset = DataErasureRequest.objects.select_related("user").all()


_LEGAL_HOLD_EXAMPLE = {
    "id": "d1e2f3a4-...",
    "user": "b6a5b6c0-...",
    "reason": "Open chargeback dispute",
    "created_at": "2026-02-01T08:00:00Z",
    "released_at": None,
}


@extend_schema(
    tags=["Admin"],
    request=LegalHoldCreateSerializer,
    responses={201: LegalHoldSerializer},
    description="Places a legal hold on a user, blocking any erasure request against their "
    "account until the hold is released.",
    examples=[
        OpenApiExample(
            "Place hold", value={"reason": "Open chargeback dispute"}, request_only=True
        ),
        OpenApiExample("Created", value=_LEGAL_HOLD_EXAMPLE, response_only=True),
    ],
)
class AdminLegalHoldCreateView(APIView):
    permission_classes = [HasPermission]
    required_permission = "privacy.manage"
    throttle_scope = "admin-write"

    def post(self, request, user_id):
        serializer = LegalHoldCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hold = services.place_legal_hold(user_id, serializer.validated_data["reason"])
        record_event(
            actor=request.user,
            action="legal_hold.create",
            entity_type="LegalHold",
            entity_id=hold.id,
            request=request,
            payload={"user_id": str(user_id)},
        )
        return Response(LegalHoldSerializer(hold).data, status=201)


@extend_schema(
    tags=["Admin"],
    request=None,
    responses={200: LegalHoldSerializer},
    description="Releases a legal hold, allowing erasure requests against the account to "
    "proceed again.",
    examples=[
        OpenApiExample(
            "Released",
            value={**_LEGAL_HOLD_EXAMPLE, "released_at": "2026-02-10T09:00:00Z"},
            response_only=True,
        )
    ],
)
class AdminLegalHoldReleaseView(APIView):
    permission_classes = [HasPermission]
    required_permission = "privacy.manage"
    throttle_scope = "admin-write"

    def post(self, request, hold_id):
        hold = services.release_legal_hold(hold_id)
        record_event(
            actor=request.user,
            action="legal_hold.release",
            entity_type="LegalHold",
            entity_id=hold.id,
            request=request,
        )
        return Response(LegalHoldSerializer(hold).data)
