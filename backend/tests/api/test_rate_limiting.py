import pytest

from apps.authorization.models import Role, UserRole

pytestmark = pytest.mark.django_db


@pytest.fixture
def student(django_user_model):
    return django_user_model.objects.create_user(email="student@example.com", password="x")


@pytest.fixture
def student_client(api_client, student):
    api_client.force_authenticate(user=student)
    return api_client


@pytest.fixture
def admin_client(api_client, django_user_model):
    admin = django_user_model.objects.create_user(email="admin@example.com", password="x")
    UserRole.objects.create(user=admin, role=Role.objects.get(code="administrator"))
    api_client.force_authenticate(user=admin)
    return api_client


class TestFinancialWriteThrottle:
    def test_exceeding_financial_write_rate_returns_429(self, student_client):
        # ApplyCouponView 404s immediately (no such order) — the point is
        # that ScopedRateThrottle counts the request in APIView.dispatch()
        # before the view body runs, so this exercises the throttle
        # without needing a real order/payment fixture.
        responses = [
            student_client.post(
                "/api/v1/checkout/orders/00000000-0000-0000-0000-000000000000/apply-coupon/",
                {"code": "X"},
                format="json",
            )
            for _ in range(21)
        ]

        assert [r.status_code for r in responses[:20]].count(429) == 0
        assert responses[20].status_code == 429


class TestAdminWriteThrottle:
    def test_exceeding_admin_write_rate_returns_429(self, admin_client):
        responses = [
            admin_client.patch(
                "/api/v1/admin/settings/", {"key": f"k{i}", "value_json": {}}, format="json"
            )
            for i in range(61)
        ]

        assert responses[60].status_code == 429


class TestBlanketAnonThrottle:
    def test_exceeding_anon_rate_returns_429(self, api_client):
        responses = [api_client.get("/api/v1/courses/") for _ in range(61)]

        assert responses[60].status_code == 429
