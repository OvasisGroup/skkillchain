from django.conf import settings
from drf_spectacular.utils import extend_schema
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


@extend_schema(
    tags=["Affiliate"],
    request=None,
    responses={201: AffiliateAccountSerializer, 200: AffiliateAccountSerializer},
)
class AffiliateRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        account, created = AffiliateAccount.objects.get_or_create(
            user=request.user,
            defaults={"commission_rate": settings.AFFILIATE_DEFAULT_COMMISSION_RATE},
        )
        return Response(AffiliateAccountSerializer(account).data, status=201 if created else 200)


@extend_schema(tags=["Affiliate"], responses={200: AffiliateAccountSerializer})
class AffiliateMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        account = _own_affiliate_account_or_403(request.user)
        return Response(AffiliateAccountSerializer(account).data)


@extend_schema(tags=["Affiliate"])
class AffiliateReferralListView(generics.ListAPIView):
    serializer_class = AffiliateReferralSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        account = _own_affiliate_account_or_403(self.request.user)
        return account.referrals.select_related("referred_user")


@extend_schema(tags=["Affiliate"])
class AffiliateCommissionListView(generics.ListAPIView):
    serializer_class = AffiliateCommissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        account = _own_affiliate_account_or_403(self.request.user)
        return AffiliateCommission.objects.filter(referral__affiliate=account)


@extend_schema(tags=["Affiliate"], responses={200: WalletSerializer})
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


@extend_schema(tags=["Affiliate"], request=None, responses={201: PayoutSerializer})
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
