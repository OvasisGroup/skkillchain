import pytest

from apps.authorization.models import Role, UserRole
from apps.platform_settings.models import Setting

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(email="user@example.com", password="x")


@pytest.fixture
def user_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin(django_user_model):
    return django_user_model.objects.create_user(email="admin@example.com", password="x")


@pytest.fixture
def admin_client(api_client, admin):
    UserRole.objects.create(user=admin, role=Role.objects.get(code="administrator"))
    api_client.force_authenticate(user=admin)
    return api_client


class TestAdminSettings:
    def test_non_admin_forbidden(self, user_client):
        response = user_client.get("/api/v1/admin/settings/")

        assert response.status_code == 403

    def test_patch_creates_setting(self, admin_client):
        response = admin_client.patch(
            "/api/v1/admin/settings/",
            {"key": "maintenance_mode", "value_json": {"enabled": False}},
            format="json",
        )

        assert response.status_code == 200
        assert Setting.objects.filter(key="maintenance_mode", scope_type="platform").exists()

    def test_patch_upserts_existing_setting(self, admin_client):
        admin_client.patch(
            "/api/v1/admin/settings/", {"key": "k", "value_json": {"v": 1}}, format="json"
        )
        admin_client.patch(
            "/api/v1/admin/settings/", {"key": "k", "value_json": {"v": 2}}, format="json"
        )

        assert Setting.objects.filter(key="k").count() == 1
        assert Setting.objects.get(key="k").value_json == {"v": 2}

    def test_list_returns_settings(self, admin_client):
        Setting.objects.create(key="existing", value_json={})

        response = admin_client.get("/api/v1/admin/settings/")

        assert response.status_code == 200
        assert len(response.data) == 1
