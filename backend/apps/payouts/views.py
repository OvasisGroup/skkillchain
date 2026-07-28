from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event

from . import services
from .models import Payout, Wallet
from .serializers import PayoutSerializer, WalletSerializer


@extend_schema(tags=["Instructor"], responses={200: WalletSerializer})
class InstructorWalletView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wallet = Wallet.objects.filter(
            owner_type=Wallet.OWNER_INSTRUCTOR, owner_id=request.user.id
        ).first()
        if wallet is None:
            return Response({"id": None, "balance_amount": "0.00", "currency": "USD"})
        return Response(WalletSerializer(wallet).data)


@extend_schema(tags=["Instructor"])
class InstructorPayoutListView(generics.ListAPIView):
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Payout.objects.filter(instructor=self.request.user)


@extend_schema(tags=["Instructor"], request=None, responses={201: PayoutSerializer})
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
