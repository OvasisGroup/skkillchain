from drf_spectacular.utils import extend_schema
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


@extend_schema(tags=["Privacy"], request=None, responses={201: DataErasureRequestSerializer})
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


@extend_schema(tags=["Admin"])
class AdminErasureRequestListView(generics.ListAPIView):
    serializer_class = DataErasureRequestSerializer
    permission_classes = [HasPermission]
    required_permission = "privacy.manage"
    pagination_class = RequestedAtCursorPagination
    queryset = DataErasureRequest.objects.select_related("user").all()


@extend_schema(
    tags=["Admin"], request=LegalHoldCreateSerializer, responses={201: LegalHoldSerializer}
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


@extend_schema(tags=["Admin"], request=None, responses={200: LegalHoldSerializer})
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
