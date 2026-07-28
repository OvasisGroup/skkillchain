import pytest
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.authorization.models import Role, UserRole
from apps.notifications.models import EmailTemplate, NotificationTemplate
from apps.support.models import SupportTicket

pytestmark = pytest.mark.django_db


def _client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def plain_user(django_user_model):
    return django_user_model.objects.create_user(email="plain@example.com", password="x")


@pytest.fixture
def plain_client(api_client, plain_user):
    api_client.force_authenticate(user=plain_user)
    return api_client


@pytest.fixture
def admin(django_user_model):
    user = django_user_model.objects.create_user(email="admin@example.com", password="x")
    UserRole.objects.create(user=user, role=Role.objects.get(code="administrator"))
    return user


@pytest.fixture
def admin_client(admin):
    return _client_for(admin)


class TestAdminUsers:
    def test_non_admin_forbidden(self, plain_client):
        response = plain_client.get("/api/v1/admin/users/")

        assert response.status_code == 403

    def test_list_and_filter_by_email(self, admin_client, plain_user):
        response = admin_client.get("/api/v1/admin/users/", {"email": "plain"})

        emails = [u["email"] for u in response.data["results"]]
        assert plain_user.email in emails

    def test_suspend_and_reinstate(self, admin_client, plain_user):
        suspend = admin_client.patch(
            f"/api/v1/admin/users/{plain_user.id}/status/", {"is_active": False}, format="json"
        )
        assert suspend.status_code == 200
        plain_user.refresh_from_db()
        assert plain_user.is_active is False

        reinstate = admin_client.patch(
            f"/api/v1/admin/users/{plain_user.id}/status/", {"is_active": True}, format="json"
        )
        assert reinstate.status_code == 200
        plain_user.refresh_from_db()
        assert plain_user.is_active is True


class TestAdminTemplates:
    def test_notification_template_list_and_update(self, admin_client):
        NotificationTemplate.objects.create(
            code="welcome", channel="email", body_template="Hi {name}"
        )

        list_response = admin_client.get("/api/v1/admin/notification-templates/")
        assert len(list_response.data) == 1

        update_response = admin_client.patch(
            "/api/v1/admin/notification-templates/welcome/",
            {"body_template": "Hello {name}!"},
            format="json",
        )
        assert update_response.status_code == 200
        assert update_response.data["body_template"] == "Hello {name}!"

    def test_email_template_list_and_update(self, admin_client):
        EmailTemplate.objects.create(code="digest", subject="Weekly digest", html_body="<p>hi</p>")

        update_response = admin_client.patch(
            "/api/v1/admin/email-templates/digest/", {"subject": "New subject"}, format="json"
        )
        assert update_response.status_code == 200
        assert update_response.data["subject"] == "New subject"

    def test_non_admin_forbidden(self, plain_client):
        response = plain_client.get("/api/v1/admin/notification-templates/")

        assert response.status_code == 403


class TestAdminSupportTickets:
    def test_list_all_tickets(self, admin_client, plain_user):
        SupportTicket.objects.create(requester=plain_user, subject="q")

        response = admin_client.get("/api/v1/admin/support-tickets/")

        assert len(response.data) == 1

    def test_assign_and_update_status(self, admin_client, plain_user, admin):
        ticket = SupportTicket.objects.create(requester=plain_user, subject="q")

        response = admin_client.patch(
            f"/api/v1/admin/support-tickets/{ticket.id}/",
            {"assignee": str(admin.id), "status": "in_progress"},
            format="json",
        )

        assert response.status_code == 200
        ticket.refresh_from_db()
        assert ticket.assignee_id == admin.id
        assert ticket.status == "in_progress"


class TestAdminAuditLogs:
    def test_list_requires_permission(self, plain_client):
        response = plain_client.get("/api/v1/admin/audit-logs/")

        assert response.status_code == 403

    def test_admin_can_list(self, admin_client, plain_user):
        AuditLog.objects.create(actor=plain_user, action="user.suspend")

        response = admin_client.get("/api/v1/admin/audit-logs/")

        assert response.status_code == 200
        assert len(response.data["results"]) >= 1
