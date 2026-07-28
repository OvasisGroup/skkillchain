from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.affiliates.models import AffiliateAccount, AffiliateCommission, AffiliateReferral
from apps.catalog.models import Course
from apps.commerce.models import GiftCard
from apps.payouts.models import Wallet

pytestmark = pytest.mark.django_db


def _client_for(user):
    # api_client/affiliate_client/buyer_client all wrap the same
    # underlying test client per test (pytest fixture caching), so a test
    # needing two independently authenticated users at once must build a
    # second APIClient explicitly rather than combining two named fixtures.
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


@pytest.fixture
def affiliate(django_user_model):
    return django_user_model.objects.create_user(email="affiliate@example.com", password="x")


@pytest.fixture
def affiliate_client(api_client, affiliate):
    api_client.force_authenticate(user=affiliate)
    return api_client


@pytest.fixture
def buyer(django_user_model):
    return django_user_model.objects.create_user(email="buyer@example.com", password="x")


@pytest.fixture
def buyer_client(api_client, buyer):
    api_client.force_authenticate(user=buyer)
    return api_client


@pytest.fixture
def course(instructor):
    c = Course.objects.create(
        owner=instructor, title="Affiliate Course", price_amount=Decimal("100.00")
    )
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


class TestAffiliateRegister:
    def test_register_creates_account_with_referral_code(self, affiliate_client):
        response = affiliate_client.post("/api/v1/affiliate/register/")

        assert response.status_code == 201
        assert len(response.data["referral_code"]) == 8

    def test_register_twice_is_idempotent(self, affiliate_client):
        first = affiliate_client.post("/api/v1/affiliate/register/")
        second = affiliate_client.post("/api/v1/affiliate/register/")

        assert first.status_code == 201
        assert second.status_code == 200
        assert first.data["referral_code"] == second.data["referral_code"]

    def test_me_requires_registration(self, buyer_client):
        response = buyer_client.get("/api/v1/affiliate/me/")

        assert response.status_code == 403


class TestReferralCaptureAndCommission:
    def test_purchase_with_referral_code_credits_affiliate_on_payment(
        self, buyer_client, affiliate, buyer, course, settings
    ):
        settings.AFFILIATE_DEFAULT_COMMISSION_RATE = Decimal("10.00")
        register_resp = _client_for(affiliate).post("/api/v1/affiliate/register/")
        code = register_resp.data["referral_code"]

        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id)}], "referral_code": code},
            format="json",
        )
        assert AffiliateReferral.objects.filter(order_id=order_resp.data["id"]).exists()

        GiftCard.objects.create(code="AFFCOVER", balance_amount=Decimal("100.00"), currency="USD")
        buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/apply-gift-card/",
            {"code": "AFFCOVER"},
            format="json",
        )
        pay_resp = buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/pay/",
            {"provider": "stripe"},
            format="json",
        )

        assert pay_resp.status_code == 200
        referral = AffiliateReferral.objects.get(order_id=order_resp.data["id"])
        assert referral.status == AffiliateReferral.STATUS_CONVERTED
        commission = AffiliateCommission.objects.get(referral=referral)
        assert commission.commission_amount == Decimal("10.00")  # 10% of $100
        wallet = Wallet.objects.get(owner_type=Wallet.OWNER_AFFILIATE, owner_id=affiliate.id)
        assert wallet.balance_amount == Decimal("10.00")

    def test_unknown_referral_code_does_not_block_checkout(self, buyer_client, course):
        response = buyer_client.post(
            "/api/v1/checkout/orders/",
            {
                "items": [{"item_type": "course", "item_id": str(course.id)}],
                "referral_code": "NOSUCHCODE",
            },
            format="json",
        )

        assert response.status_code == 201
        assert not AffiliateReferral.objects.filter(order_id=response.data["id"]).exists()

    def test_self_referral_is_ignored(self, buyer_client, buyer, course):
        AffiliateAccount.objects.create(
            user=buyer, referral_code="SELFCODE", commission_rate=Decimal("10.00")
        )

        response = buyer_client.post(
            "/api/v1/checkout/orders/",
            {
                "items": [{"item_type": "course", "item_id": str(course.id)}],
                "referral_code": "SELFCODE",
            },
            format="json",
        )

        assert not AffiliateReferral.objects.filter(order_id=response.data["id"]).exists()


class TestAffiliateWalletAndPayout:
    def test_wallet_and_payout_flow(self, affiliate_client, affiliate):
        affiliate_client.post("/api/v1/affiliate/register/")
        from apps.payouts import services

        services.credit_affiliate_wallet(
            affiliate.id, amount=Decimal("42.00"), currency="USD", reason="affiliate_commission"
        )

        wallet_resp = affiliate_client.get("/api/v1/affiliate/wallet/")
        assert wallet_resp.data["balance_amount"] == "42.00"

        payout_resp = affiliate_client.post("/api/v1/affiliate/payout-requests/")
        assert payout_resp.status_code == 201
        assert payout_resp.data["amount_net"] == "42.00"

        wallet_resp_after = affiliate_client.get("/api/v1/affiliate/wallet/")
        assert wallet_resp_after.data["balance_amount"] == "0.00"

    def test_payout_request_requires_affiliate_registration(self, buyer_client):
        response = buyer_client.post("/api/v1/affiliate/payout-requests/")

        assert response.status_code == 403

    def test_referral_and_commission_listing(self, buyer_client, affiliate, buyer, course):
        affiliate_client = _client_for(affiliate)
        register_resp = affiliate_client.post("/api/v1/affiliate/register/")
        code = register_resp.data["referral_code"]
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id)}], "referral_code": code},
            format="json",
        )
        GiftCard.objects.create(code="LISTCOVER", balance_amount=Decimal("100.00"), currency="USD")
        buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/apply-gift-card/",
            {"code": "LISTCOVER"},
            format="json",
        )
        buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/pay/",
            {"provider": "stripe"},
            format="json",
        )

        referrals = affiliate_client.get("/api/v1/affiliate/referrals/")
        commissions = affiliate_client.get("/api/v1/affiliate/commissions/")

        assert len(referrals.data) == 1
        assert referrals.data[0]["status"] == "converted"
        assert len(commissions.data) == 1
