from decimal import Decimal

import pytest

from apps.catalog.models import Course
from apps.payouts.models import Payout, Wallet

pytestmark = pytest.mark.django_db


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


@pytest.fixture
def instructor_client(api_client, instructor):
    api_client.force_authenticate(user=instructor)
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
        owner=instructor, title="Payout Course", price_amount=Decimal("100.00")
    )
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


class TestCourseSaleCreditsInstructorWallet:
    def test_full_purchase_flow_credits_instructor_at_configured_commission_rate(
        self, buyer_client, instructor, course, settings
    ):
        settings.PLATFORM_COMMISSION_RATE = Decimal("0.30")
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id)}]},
            format="json",
        )
        from apps.commerce.models import GiftCard

        GiftCard.objects.create(
            code="PAYOUTCOVER", balance_amount=Decimal("100.00"), currency="USD"
        )
        buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/apply-gift-card/",
            {"code": "PAYOUTCOVER"},
            format="json",
        )

        response = buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/pay/",
            {"provider": "stripe"},
            format="json",
        )

        assert response.status_code == 200
        wallet = Wallet.objects.get(owner_type=Wallet.OWNER_INSTRUCTOR, owner_id=instructor.id)
        assert wallet.balance_amount == Decimal("70.00")  # 100 * (1 - 0.30)


class TestInstructorWalletView:
    def test_no_wallet_yet_returns_zero_balance(self, instructor_client):
        response = instructor_client.get("/api/v1/instructor/wallet/")

        assert response.status_code == 200
        assert response.data["balance_amount"] == "0.00"

    def test_shows_real_balance(self, instructor_client, instructor):
        from apps.payouts import services

        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("55.00"), currency="USD", reason="course_sale"
        )

        response = instructor_client.get("/api/v1/instructor/wallet/")

        assert response.data["balance_amount"] == "55.00"


class TestPayoutRequestAndList:
    def test_request_payout_creates_paid_payout(self, instructor_client, instructor):
        from apps.payouts import services

        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("88.00"), currency="USD", reason="course_sale"
        )

        response = instructor_client.post("/api/v1/instructor/payout-requests/")

        assert response.status_code == 201
        assert response.data["amount_net"] == "88.00"
        assert response.data["status"] == "paid"

    def test_request_payout_with_no_balance_rejected(self, instructor_client):
        response = instructor_client.post("/api/v1/instructor/payout-requests/")

        assert response.status_code == 400

    def test_payout_list_only_shows_own_payouts(
        self, instructor_client, instructor, django_user_model
    ):
        other = django_user_model.objects.create_user(email="other@example.com", password="x")
        from apps.payouts import services

        services.credit_instructor_wallet(
            other.id, amount=Decimal("10.00"), currency="USD", reason="course_sale"
        )
        services.request_payout(other)
        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("20.00"), currency="USD", reason="course_sale"
        )
        services.request_payout(instructor)

        response = instructor_client.get("/api/v1/instructor/payouts/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert Payout.objects.count() == 2  # both exist; only one's own
