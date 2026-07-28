from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event

from . import services
from .models import Payout, Wallet
from .serializers import PayoutSerializer, WalletSerializer

_PAYOUT_EXAMPLE = {
    "id": "b1c2d3e4-...",
    "period_start": "2026-01-01",
    "period_end": "2026-01-31",
    "amount_gross": "1200.00",
    "amount_net": "1080.00",
    "status": "requested",
    "paid_at": None,
    "created_at": "2026-02-01T09:00:00Z",
}


@extend_schema(
    tags=["Instructor"],
    responses={200: WalletSerializer},
    description="Gets the current instructor's wallet balance (available for payout). Returns "
    "a zero balance if no wallet has been created yet (no earnings recorded so far).",
    examples=[
        OpenApiExample(
            "Wallet",
            value={"id": "c2d3e4f5-...", "balance_amount": "1200.00", "currency": "USD"},
            response_only=True,
        )
    ],
)
class InstructorWalletView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wallet = Wallet.objects.filter(
            owner_type=Wallet.OWNER_INSTRUCTOR, owner_id=request.user.id
        ).first()
        if wallet is None:
            return Response({"id": None, "balance_amount": "0.00", "currency": "USD"})
        return Response(WalletSerializer(wallet).data)


@extend_schema(
    tags=["Instructor"],
    description="Lists the current instructor's past payouts.",
    examples=[OpenApiExample("Payout", value=_PAYOUT_EXAMPLE, response_only=True)],
)
class InstructorPayoutListView(generics.ListAPIView):
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Payout.objects.filter(instructor=self.request.user)


@extend_schema(
    tags=["Instructor"],
    request=None,
    responses={201: PayoutSerializer},
    description="Requests a payout of the current instructor's full available wallet balance "
    "for the elapsed earning period, net of the platform commission.",
    examples=[OpenApiExample("Requested", value=_PAYOUT_EXAMPLE, response_only=True)],
)
class InstructorPayoutRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "financial-write"

    def post(self, request):
        payout = services.request_payout(request.user)
        record_event(
            actor=request.user,
            action="payout.request",
            entity_type="Payout",
            entity_id=payout.id,
            request=request,
            payload={"amount_net": str(payout.amount_net)},
        )
        return Response(PayoutSerializer(payout).data, status=201)
