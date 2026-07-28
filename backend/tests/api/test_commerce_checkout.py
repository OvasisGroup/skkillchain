import hashlib
import hmac
import json
import time
from decimal import Decimal

import pytest

from apps.authorization.models import Role, UserRole
from apps.catalog.models import Course
from apps.commerce.models import Coupon, GiftCard, Order, Payment, WebhookEvent
from apps.learning.models import Enrollment

pytestmark = pytest.mark.django_db


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


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
        owner=instructor, title="Checkout Course", price_amount=Decimal("50.00")
    )
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


class TestCheckoutOrderCreate:
    def test_creates_order_priced_from_real_course(self, buyer_client, course):
        response = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id), "quantity": 1}]},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["subtotal_amount"] == "50.00"
        assert response.data["total_amount"] == "50.00"

    def test_requires_authentication(self, api_client, course):
        response = api_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id), "quantity": 1}]},
            format="json",
        )

        assert response.status_code == 401

    def test_rejects_empty_items(self, buyer_client):
        response = buyer_client.post("/api/v1/checkout/orders/", {"items": []}, format="json")

        assert response.status_code == 400


class TestApplyCouponAndGiftCard:
    def test_apply_coupon_recomputes_total(self, buyer_client, course, instructor):
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id)}]},
            format="json",
        )
        Coupon.objects.create(
            code="SAVE20",
            discount_type=Coupon.DISCOUNT_PERCENT,
            discount_value=Decimal("20"),
            created_by=instructor,
        )

        response = buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/apply-coupon/",
            {"code": "SAVE20"},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["total_amount"] == "40.00"

    def test_apply_gift_card_recomputes_total(self, buyer_client, course):
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id)}]},
            format="json",
        )
        GiftCard.objects.create(code="GIFT1", balance_amount=Decimal("15.00"), currency="USD")

        response = buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/apply-gift-card/",
            {"code": "GIFT1"},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["gift_card_amount"] == "15.00"
        assert response.data["total_amount"] == "35.00"

    def test_apply_coupon_on_someone_elses_order_is_404(
        self, buyer_client, django_user_model, course
    ):
        other = django_user_model.objects.create_user(email="other@example.com", password="x")
        other_order = Order.objects.create(buyer=other, currency="USD")

        response = buyer_client.post(
            f"/api/v1/checkout/orders/{other_order.id}/apply-coupon/", {"code": "X"}, format="json"
        )

        assert response.status_code == 404


class TestPayOrder:
    def test_zero_total_order_finalizes_without_calling_a_provider(
        self, buyer_client, course, buyer
    ):
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id)}]},
            format="json",
        )
        GiftCard.objects.create(code="FULLCOVER", balance_amount=Decimal("999.00"), currency="USD")
        buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/apply-gift-card/",
            {"code": "FULLCOVER"},
            format="json",
        )

        response = buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/pay/",
            {"provider": "stripe"},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["payment"]["status"] == "succeeded"
        order = Order.objects.get(id=order_resp.data["id"])
        assert order.status == Order.STATUS_PAID
        assert Enrollment.objects.filter(student=buyer, course=course).exists()

    def test_pay_with_real_provider_call(self, buyer_client, course, monkeypatch, settings):
        settings.STRIPE_SECRET_KEY = "sk_test"
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id)}]},
            format="json",
        )

        class FakeResponse:
            status_code = 200

            def json(self):
                return {"id": "pi_123", "client_secret": "secret_123"}

        monkeypatch.setattr(
            "apps.commerce.providers.stripe.requests.post", lambda *a, **k: FakeResponse()
        )

        response = buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/pay/",
            {"provider": "stripe"},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["client_secret"] == "secret_123"
        payment = Payment.objects.get(order_id=order_resp.data["id"])
        assert payment.status == Payment.STATUS_PENDING
        assert payment.provider_payment_id == "pi_123"

    def test_cannot_pay_an_already_paid_order(self, buyer_client, course):
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id)}]},
            format="json",
        )
        order = Order.objects.get(id=order_resp.data["id"])
        order.status = Order.STATUS_PAID
        order.save(update_fields=["status"])

        response = buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/pay/",
            {"provider": "stripe"},
            format="json",
        )

        assert response.status_code == 400


class TestStripeWebhookEndToEnd:
    def _post_stripe_event(self, api_client, event_id, event_type, provider_payment_id, secret):
        payload = json.dumps(
            {"id": event_id, "type": event_type, "data": {"object": {"id": provider_payment_id}}}
        )
        timestamp = str(int(time.time()))
        signed_payload = f"{timestamp}.{payload}".encode()
        signature = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        return api_client.post(
            "/api/v1/webhooks/stripe/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=f"t={timestamp},v1={signature}",
        )

    def test_webhook_without_signature_rejected(self, api_client):
        response = api_client.post(
            "/api/v1/webhooks/stripe/",
            data=json.dumps(
                {
                    "id": "evt_x",
                    "type": "payment_intent.succeeded",
                    "data": {"object": {"id": "pi_x"}},
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_valid_webhook_marks_payment_succeeded_and_finalizes_order(
        self, api_client, buyer_client, course, buyer, settings
    ):
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id)}]},
            format="json",
        )
        payment = Payment.objects.create(
            order_id=order_resp.data["id"],
            provider="stripe",
            provider_payment_id="pi_live_1",
            status=Payment.STATUS_PENDING,
            amount=Decimal("50.00"),
            currency="USD",
        )

        response = self._post_stripe_event(
            api_client, "evt_live_1", "payment_intent.succeeded", "pi_live_1", "whsec_test"
        )

        assert response.status_code == 200
        payment.refresh_from_db()
        assert payment.status == Payment.STATUS_SUCCEEDED
        assert Enrollment.objects.filter(student=buyer, course=course).exists()

    def test_replayed_event_is_idempotent(self, api_client, buyer_client, course, settings):
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id)}]},
            format="json",
        )
        Payment.objects.create(
            order_id=order_resp.data["id"],
            provider="stripe",
            provider_payment_id="pi_replay",
            status=Payment.STATUS_PENDING,
            amount=Decimal("50.00"),
            currency="USD",
        )

        first = self._post_stripe_event(
            api_client, "evt_replay_1", "payment_intent.succeeded", "pi_replay", "whsec_test"
        )
        second = self._post_stripe_event(
            api_client, "evt_replay_1", "payment_intent.succeeded", "pi_replay", "whsec_test"
        )

        assert first.status_code == 200
        assert second.status_code == 200
        assert second.data["status"] == "already_processed"
        assert (
            WebhookEvent.objects.filter(provider="stripe", provider_event_id="evt_replay_1").count()
            == 1
        )
        # Enrollment created exactly once despite the replay.
        assert Enrollment.objects.filter(course=course).count() == 1


class TestRefund:
    def test_refund_succeeds_and_marks_order_refunded(self, buyer_client, course, monkeypatch):
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id)}]},
            format="json",
        )
        order = Order.objects.get(id=order_resp.data["id"])
        payment = Payment.objects.create(
            order=order,
            provider="stripe",
            provider_payment_id="pi_refundme",
            status=Payment.STATUS_SUCCEEDED,
            amount=Decimal("50.00"),
            currency="USD",
        )

        class FakeResponse:
            status_code = 200

            def json(self):
                return {"id": "re_1", "status": "succeeded"}

        monkeypatch.setattr(
            "apps.commerce.providers.stripe.requests.post", lambda *a, **k: FakeResponse()
        )

        response = buyer_client.post(
            "/api/v1/refunds/",
            {"payment_id": str(payment.id), "amount": "50.00", "reason": "changed my mind"},
            format="json",
        )

        assert response.status_code == 201
        payment.refresh_from_db()
        order.refresh_from_db()
        assert payment.status == Payment.STATUS_REFUNDED
        assert order.status == Order.STATUS_REFUNDED

    def test_cannot_refund_someone_elses_payment(self, buyer_client, django_user_model, course):
        other = django_user_model.objects.create_user(email="other@example.com", password="x")
        other_order = Order.objects.create(buyer=other, currency="USD")
        payment = Payment.objects.create(
            order=other_order,
            provider="stripe",
            provider_payment_id="pi_notyours",
            status=Payment.STATUS_SUCCEEDED,
            amount=Decimal("50.00"),
            currency="USD",
        )

        response = buyer_client.post(
            "/api/v1/refunds/", {"payment_id": str(payment.id), "amount": "50.00"}, format="json"
        )

        assert response.status_code == 404

    def test_cannot_refund_more_than_paid(self, buyer_client, course):
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "course", "item_id": str(course.id)}]},
            format="json",
        )
        payment = Payment.objects.create(
            order_id=order_resp.data["id"],
            provider="stripe",
            provider_payment_id="pi_x",
            status=Payment.STATUS_SUCCEEDED,
            amount=Decimal("50.00"),
            currency="USD",
        )

        response = buyer_client.post(
            "/api/v1/refunds/", {"payment_id": str(payment.id), "amount": "9999.00"}, format="json"
        )

        assert response.status_code == 400


class TestAdminCouponsAndPromotions:
    def test_finance_officer_can_create_platform_coupon(self, api_client, django_user_model):
        officer = django_user_model.objects.create_user(email="finance@example.com", password="x")
        UserRole.objects.create(user=officer, role=Role.objects.get(code="finance_officer"))
        api_client.force_authenticate(user=officer)

        response = api_client.post(
            "/api/v1/admin/coupons/",
            {"code": "PLATFORM10", "discount_type": "percent", "discount_value": "10"},
            format="json",
        )

        assert response.status_code == 201

    def test_regular_buyer_cannot_create_platform_coupon(self, buyer_client):
        response = buyer_client.post(
            "/api/v1/admin/coupons/",
            {"code": "NOPE", "discount_type": "percent", "discount_value": "10"},
            format="json",
        )

        assert response.status_code == 403


class TestInstructorCourseCoupon:
    def test_owner_can_create_course_scoped_coupon(self, api_client, instructor, course):
        api_client.force_authenticate(user=instructor)

        response = api_client.post(
            f"/api/v1/instructor/courses/{course.id}/coupons/",
            {"code": "COURSE10", "discount_type": "percent", "discount_value": "10"},
            format="json",
        )

        assert response.status_code == 201
        assert Coupon.objects.get(code="COURSE10").course_id == course.id

    def test_non_owner_cannot_create_course_scoped_coupon(self, buyer_client, course):
        response = buyer_client.post(
            f"/api/v1/instructor/courses/{course.id}/coupons/",
            {"code": "NOPE", "discount_type": "percent", "discount_value": "10"},
            format="json",
        )

        assert response.status_code == 403


class TestGiftCardBalanceLookup:
    def test_public_lookup_by_code(self, api_client):
        GiftCard.objects.create(code="LOOKUP1", balance_amount=Decimal("25.00"), currency="USD")

        response = api_client.get("/api/v1/gift-cards/LOOKUP1/")

        assert response.status_code == 200
        assert response.data["balance_amount"] == "25.00"
