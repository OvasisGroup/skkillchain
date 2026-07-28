from decimal import Decimal

import pytest

from apps.billing.models import Plan, Subscription

pytestmark = pytest.mark.django_db


@pytest.fixture
def buyer(django_user_model):
    return django_user_model.objects.create_user(email="buyer@example.com", password="x")


@pytest.fixture
def buyer_client(api_client, buyer):
    api_client.force_authenticate(user=buyer)
    return api_client


@pytest.fixture
def plan():
    return Plan.objects.create(
        code="pro-monthly",
        name="Pro Monthly",
        billing_interval=Plan.INTERVAL_MONTHLY,
        price_amount=Decimal("19.99"),
        currency="USD",
    )


class TestPlanList:
    def test_lists_active_plans_publicly(self, api_client, plan):
        response = api_client.get("/api/v1/plans/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["code"] == "pro-monthly"

    def test_excludes_inactive_plans(self, api_client, plan):
        plan.is_active = False
        plan.save(update_fields=["is_active"])

        response = api_client.get("/api/v1/plans/")

        assert response.data == []


class TestPlanPurchaseViaCheckout:
    def test_order_for_a_plan_is_priced_from_the_real_plan_record(self, buyer_client, plan):
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "plan", "item_id": str(plan.id)}]},
            format="json",
        )

        assert order_resp.status_code == 201
        assert order_resp.data["total_amount"] == "19.99"

    def test_zero_priced_plan_activates_subscription_immediately(self, buyer_client, buyer):
        free_plan = Plan.objects.create(
            code="free",
            name="Free",
            billing_interval=Plan.INTERVAL_MONTHLY,
            price_amount=Decimal("0"),
        )
        order_resp = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "plan", "item_id": str(free_plan.id)}]},
            format="json",
        )
        assert order_resp.data["total_amount"] == "0.00"

        pay_resp = buyer_client.post(
            f"/api/v1/checkout/orders/{order_resp.data['id']}/pay/",
            {"provider": "stripe"},
            format="json",
        )

        assert pay_resp.status_code == 200
        subscription = Subscription.objects.get(subscriber_id=buyer.id, plan=free_plan)
        assert subscription.status == Subscription.STATUS_ACTIVE
        assert subscription.renews_at is not None

    def test_rejects_inactive_plan(self, buyer_client, plan):
        plan.is_active = False
        plan.save(update_fields=["is_active"])

        response = buyer_client.post(
            "/api/v1/checkout/orders/",
            {"items": [{"item_type": "plan", "item_id": str(plan.id)}]},
            format="json",
        )

        assert response.status_code == 400


class TestSubscriptionListAndCancel:
    def test_list_only_shows_own_subscriptions(self, buyer_client, buyer, plan, django_user_model):
        other = django_user_model.objects.create_user(email="other@example.com", password="x")
        Subscription.objects.create(
            subscriber_type=Subscription.SUBSCRIBER_USER, subscriber_id=other.id, plan=plan
        )
        Subscription.objects.create(
            subscriber_type=Subscription.SUBSCRIBER_USER, subscriber_id=buyer.id, plan=plan
        )

        response = buyer_client.get("/api/v1/subscriptions/")

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_cancel_own_subscription(self, buyer_client, buyer, plan):
        subscription = Subscription.objects.create(
            subscriber_type=Subscription.SUBSCRIBER_USER, subscriber_id=buyer.id, plan=plan
        )

        response = buyer_client.patch(f"/api/v1/subscriptions/{subscription.id}/cancel/")

        assert response.status_code == 200
        subscription.refresh_from_db()
        assert subscription.status == Subscription.STATUS_CANCELED
        assert subscription.canceled_at is not None

    def test_cannot_cancel_someone_elses_subscription(self, buyer_client, plan, django_user_model):
        other = django_user_model.objects.create_user(email="other@example.com", password="x")
        subscription = Subscription.objects.create(
            subscriber_type=Subscription.SUBSCRIBER_USER, subscriber_id=other.id, plan=plan
        )

        response = buyer_client.patch(f"/api/v1/subscriptions/{subscription.id}/cancel/")

        assert response.status_code == 403

    def test_cannot_cancel_already_canceled_subscription(self, buyer_client, buyer, plan):
        subscription = Subscription.objects.create(
            subscriber_type=Subscription.SUBSCRIBER_USER,
            subscriber_id=buyer.id,
            plan=plan,
            status=Subscription.STATUS_CANCELED,
        )

        response = buyer_client.patch(f"/api/v1/subscriptions/{subscription.id}/cancel/")

        assert response.status_code == 400
