from django.conf import settings
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payouts import services as payout_services
from apps.payouts.models import Wallet
from apps.payouts.serializers import PayoutSerializer, WalletSerializer

from .models import AffiliateAccount, AffiliateCommission
from .serializers import (
    AffiliateAccountSerializer,
    AffiliateCommissionSerializer,
    AffiliateReferralSerializer,
)


def _own_affiliate_account_or_403(user) -> AffiliateAccount:
    account = AffiliateAccount.objects.filter(user=user).first()
    if account is None:
        raise PermissionDenied("You are not registered as an affiliate.")
    return account


_AFFILIATE_ACCOUNT_EXAMPLE = {
    "id": "d3e4f5a6-...",
    "referral_code": "AFF-JANE01",
    "commission_rate": "0.10",
}


@extend_schema(
    tags=["Affiliate"],
    request=None,
    responses={201: AffiliateAccountSerializer, 200: AffiliateAccountSerializer},
    description="Registers the current user as an affiliate, issuing a referral code. "
    "Returns 200 (not 201) if already registered.",
    examples=[OpenApiExample("Account", value=_AFFILIATE_ACCOUNT_EXAMPLE, response_only=True)],
)
class AffiliateRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        account, created = AffiliateAccount.objects.get_or_create(
            user=request.user,
            defaults={"commission_rate": settings.AFFILIATE_DEFAULT_COMMISSION_RATE},
        )
        return Response(AffiliateAccountSerializer(account).data, status=201 if created else 200)


@extend_schema(
    tags=["Affiliate"],
    responses={200: AffiliateAccountSerializer},
    description="Gets the current user's own affiliate account. 403 if not registered as an "
    "affiliate yet — see POST /affiliate/register.",
    examples=[OpenApiExample("Account", value=_AFFILIATE_ACCOUNT_EXAMPLE, response_only=True)],
)
class AffiliateMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        account = _own_affiliate_account_or_403(request.user)
        return Response(AffiliateAccountSerializer(account).data)


@extend_schema(
    tags=["Affiliate"],
    description="Lists the current affiliate's referrals (users who signed up or purchased "
    "through their referral code).",
    examples=[
        OpenApiExample(
            "Referral",
            value={
                "id": "e4f5a6b7-...",
                "referred_user_email": "newuser@example.com",
                "order": "e1f2a3b4-...",
                "status": "converted",
                "created_at": "2026-02-01T12:00:00Z",
            },
            response_only=True,
        )
    ],
)
class AffiliateReferralListView(generics.ListAPIView):
    serializer_class = AffiliateReferralSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        account = _own_affiliate_account_or_403(self.request.user)
        return account.referrals.select_related("referred_user")


@extend_schema(
    tags=["Affiliate"],
    description="Lists the current affiliate's earned commissions.",
    examples=[
        OpenApiExample(
            "Commission",
            value={
                "id": "f5a6b7c8-...",
                "referral": "e4f5a6b7-...",
                "commission_amount": "5.00",
                "payout_status": "pending",
                "created_at": "2026-02-01T12:05:00Z",
            },
            response_only=True,
        )
    ],
)
class AffiliateCommissionListView(generics.ListAPIView):
    serializer_class = AffiliateCommissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        account = _own_affiliate_account_or_403(self.request.user)
        return AffiliateCommission.objects.filter(referral__affiliate=account)


@extend_schema(
    tags=["Affiliate"],
    responses={200: WalletSerializer},
    description="Gets the current affiliate's wallet balance (available for payout).",
    examples=[
        OpenApiExample(
            "Wallet",
            value={"id": "a6b7c8d9-...", "balance_amount": "35.00", "currency": "USD"},
            response_only=True,
        )
    ],
)
class AffiliateWalletView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        _own_affiliate_account_or_403(request.user)
        wallet = Wallet.objects.filter(
            owner_type=Wallet.OWNER_AFFILIATE, owner_id=request.user.id
        ).first()
        if wallet is None:
            return Response({"id": None, "balance_amount": "0.00", "currency": "USD"})
        return Response(WalletSerializer(wallet).data)


@extend_schema(
    tags=["Affiliate"],
    request=None,
    responses={201: PayoutSerializer},
    description="Requests a payout of the current affiliate's full available wallet balance, "
    "marking every pending commission as paid.",
    examples=[
        OpenApiExample(
            "Requested",
            value={
                "id": "b7c8d9e0-...",
                "period_start": "2026-01-01",
                "period_end": "2026-01-31",
                "amount_gross": "35.00",
                "amount_net": "35.00",
                "status": "requested",
                "paid_at": None,
                "created_at": "2026-02-01T09:00:00Z",
            },
            response_only=True,
        )
    ],
)
class AffiliatePayoutRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "financial-write"

    def post(self, request):
        _own_affiliate_account_or_403(request.user)
        payout = payout_services.request_payout(request.user, owner_type=Wallet.OWNER_AFFILIATE)
        # request_payout sweeps the wallet's *entire* balance, so every
        # commission pending at this moment is covered by this payout —
        # best-effort sync rather than a precise per-transaction link
        # (AffiliateCommission isn't linked to its Transaction row
        # directly). A commission created in the narrow race window
        # between the sweep and this update could be marked paid a beat
        # early; acceptable for this internal-ledger-only implementation.
        AffiliateCommission.objects.filter(
            referral__affiliate__user=request.user,
            payout_status=AffiliateCommission.PAYOUT_STATUS_PENDING,
        ).update(payout_status=AffiliateCommission.PAYOUT_STATUS_PAID)
        return Response(PayoutSerializer(payout).data, status=201)
