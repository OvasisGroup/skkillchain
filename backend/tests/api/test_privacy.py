import pytest

from apps.commerce.models import Order, Payment
from apps.identity.models import MFAFactor, OAuthIdentity, Profile
from apps.privacy.models import DataErasureRequest, LegalHold

pytestmark = pytest.mark.django_db


@pytest.fixture
def student(django_user_model):
    return django_user_model.objects.create_user(email="student@example.com", password="x")


@pytest.fixture
def student_client(api_client, student):
    api_client.force_authenticate(user=student)
    return api_client


@pytest.fixture
def admin_user(django_user_model):
    from apps.authorization.models import Role, UserRole

    user = django_user_model.objects.create_user(email="admin@example.com", password="x")
    UserRole.objects.create(user=user, role=Role.objects.get(code="administrator"))
    return user


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


def _real_order_and_payment(student):
    order = Order.objects.create(
        buyer=student,
        subtotal_amount="100.00",
        total_amount="100.00",
        status=Order.STATUS_PAID,
    )
    payment = Payment.objects.create(
        order=order, provider="stripe", amount="100.00", status=Payment.STATUS_SUCCEEDED
    )
    return order, payment


class TestSelfServiceErasure:
    def test_erasure_anonymizes_pii_but_preserves_financial_records(self, student_client, student):
        # A real account with real financial history — exactly what the
        # workflow must be exercised against, not a bare user row.
        order, payment = _real_order_and_payment(student)
        OAuthIdentity.objects.create(
            user=student, provider=OAuthIdentity.PROVIDER_GOOGLE, provider_user_id="g-123"
        )
        MFAFactor.objects.create(user=student, secret_encrypted="enc:whatever")
        Profile.objects.filter(user=student).update(first_name="Ada", last_name="Lovelace")
        original_id = student.id

        response = student_client.post("/api/v1/privacy/erasure-requests/")

        assert response.status_code == 201
        assert response.data["status"] == DataErasureRequest.STATUS_COMPLETED

        student.refresh_from_db()
        assert student.id == original_id
        assert student.email == f"erased-user-{original_id}@erased.invalid"
        assert student.is_active is False
        assert not student.has_usable_password()

        profile = Profile.objects.get(user=student)
        assert profile.first_name == ""
        assert profile.last_name == ""
        assert not OAuthIdentity.objects.filter(user=student).exists()
        assert not MFAFactor.objects.filter(user=student).exists()

        order.refresh_from_db()
        payment.refresh_from_db()
        assert order.buyer_id == original_id
        assert payment.order_id == order.id
        assert order.status == Order.STATUS_PAID

    def test_erasure_request_requires_authentication(self, api_client):
        response = api_client.post("/api/v1/privacy/erasure-requests/")

        assert response.status_code == 401


class TestLegalHoldBlocksErasure:
    def test_active_legal_hold_blocks_erasure(self, student_client, student):
        LegalHold.objects.create(user=student, reason="Open chargeback dispute")

        response = student_client.post("/api/v1/privacy/erasure-requests/")

        assert response.status_code == 201
        assert response.data["status"] == DataErasureRequest.STATUS_BLOCKED
        assert response.data["block_reason"] == "Open chargeback dispute"

        student.refresh_from_db()
        assert student.email == "student@example.com"
        assert student.is_active is True

    def test_released_hold_no_longer_blocks(self, student_client, student):
        hold = LegalHold.objects.create(user=student, reason="Resolved matter")
        hold.released_at = hold.created_at
        hold.save(update_fields=["released_at"])

        response = student_client.post("/api/v1/privacy/erasure-requests/")

        assert response.status_code == 201
        assert response.data["status"] == DataErasureRequest.STATUS_COMPLETED


class TestAdminLegalHoldManagement:
    def test_non_admin_cannot_place_legal_hold(self, student_client, student):
        response = student_client.post(
            f"/api/v1/admin/privacy/legal-holds/{student.id}/",
            {"reason": "Investigation"},
            format="json",
        )

        assert response.status_code == 403

    def test_admin_can_place_and_release_legal_hold(self, admin_client, student):
        create_response = admin_client.post(
            f"/api/v1/admin/privacy/legal-holds/{student.id}/",
            {"reason": "Fraud investigation"},
            format="json",
        )
        assert create_response.status_code == 201
        hold_id = create_response.data["id"]
        assert LegalHold.objects.get(id=hold_id).is_active is True

        release_response = admin_client.post(
            f"/api/v1/admin/privacy/legal-holds/{hold_id}/release/"
        )
        assert release_response.status_code == 200

        hold = LegalHold.objects.get(id=hold_id)
        assert hold.is_active is False

    def test_non_admin_cannot_list_erasure_requests(self, student_client):
        response = student_client.get("/api/v1/admin/privacy/erasure-requests/")

        assert response.status_code == 403

    def test_admin_can_list_erasure_requests(self, admin_client, student):
        # admin_client and student_client both depend on the shared
        # api_client fixture instance, so authenticating one clobbers the
        # other — use a fresh client for the student side instead.
        student_only_client = admin_client.__class__()
        student_only_client.force_authenticate(user=student)
        student_only_client.post("/api/v1/privacy/erasure-requests/")

        response = admin_client.get("/api/v1/admin/privacy/erasure-requests/")

        assert response.status_code == 200
        assert len(response.data["results"]) == 1
