import pytest
from rest_framework.test import APIClient

from apps.authorization.models import Role, UserRole
from apps.moderation.models import InstructorApplication

pytestmark = pytest.mark.django_db


def _client_for(user):
    # api_client/applicant_client/moderator_client all wrap the same
    # underlying test client per test (pytest fixture caching), so a test
    # needing two independently authenticated users at once must build a
    # second APIClient explicitly rather than combining two named fixtures.
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def applicant(django_user_model):
    return django_user_model.objects.create_user(email="applicant@example.com", password="x")


@pytest.fixture
def applicant_client(api_client, applicant):
    api_client.force_authenticate(user=applicant)
    return api_client


@pytest.fixture
def moderator(django_user_model):
    user = django_user_model.objects.create_user(email="moderator@example.com", password="x")
    UserRole.objects.create(user=user, role=Role.objects.get(code="moderator"))
    return user


class TestInstructorApplication:
    def test_apply_creates_pending_application(self, applicant_client, applicant):
        response = applicant_client.post("/api/v1/instructor/apply/")

        assert response.status_code == 201
        assert response.data["status"] == "pending"
        assert InstructorApplication.objects.filter(user=applicant, status="pending").exists()

    def test_apply_twice_is_idempotent(self, applicant_client):
        first = applicant_client.post("/api/v1/instructor/apply/")
        second = applicant_client.post("/api/v1/instructor/apply/")

        assert first.data["id"] == second.data["id"]

    def test_non_moderator_cannot_list_applications(self, applicant_client):
        response = applicant_client.get("/api/v1/admin/instructors/")

        assert response.status_code == 403

    def test_moderator_can_list_and_approve(self, moderator, applicant):
        _client_for(applicant).post("/api/v1/instructor/apply/")
        moderator_client = _client_for(moderator)

        list_response = moderator_client.get("/api/v1/admin/instructors/?status=pending")
        assert len(list_response.data["results"]) == 1

        approve_response = moderator_client.post(f"/api/v1/admin/instructors/{applicant.id}/approve/")

        assert approve_response.status_code == 200
        assert approve_response.data["status"] == "approved"
        assert UserRole.objects.filter(user=applicant, role__code="instructor").exists()
