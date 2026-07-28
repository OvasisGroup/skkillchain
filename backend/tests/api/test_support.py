import pytest

from apps.notifications.models import Notification
from apps.support.models import SupportTicket, SupportTicketMessage

pytestmark = pytest.mark.django_db


@pytest.fixture
def alice(django_user_model):
    return django_user_model.objects.create_user(email="alice@example.com", password="x")


@pytest.fixture
def agent(django_user_model):
    return django_user_model.objects.create_user(email="agent@example.com", password="x")


@pytest.fixture
def eve(django_user_model):
    return django_user_model.objects.create_user(email="eve@example.com", password="x")


@pytest.fixture
def alice_client(api_client, alice):
    api_client.force_authenticate(user=alice)
    return api_client


class TestSupportTicketCreate:
    def test_create_ticket_with_initial_message(self, alice_client, alice):
        response = alice_client.post(
            "/api/v1/support-tickets/",
            {
                "category": "billing",
                "priority": "high",
                "subject": "Refund question",
                "body": "I was charged twice.",
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["status"] == "open"
        ticket = SupportTicket.objects.get(id=response.data["id"])
        assert ticket.requester == alice
        assert SupportTicketMessage.objects.filter(
            ticket=ticket, body="I was charged twice."
        ).exists()

    def test_list_only_shows_own_tickets(self, alice_client, alice, eve):
        mine = SupportTicket.objects.create(requester=alice, subject="mine")
        SupportTicket.objects.create(requester=eve, subject="not mine")

        response = alice_client.get("/api/v1/support-tickets/")

        ids = [t["id"] for t in response.data["results"]]
        assert str(mine.id) in ids
        assert len(ids) == 1


class TestSupportTicketMessages:
    def test_non_party_cannot_view_messages(self, alice_client, alice, eve):
        ticket = SupportTicket.objects.create(requester=eve, subject="not yours")

        response = alice_client.get(f"/api/v1/support-tickets/{ticket.id}/messages/")

        assert response.status_code == 403

    def test_requester_reply_does_not_flip_status_and_notifies_assignee(
        self, alice_client, alice, agent
    ):
        ticket = SupportTicket.objects.create(requester=alice, assignee=agent, subject="q")

        response = alice_client.post(
            f"/api/v1/support-tickets/{ticket.id}/messages/", {"body": "any update?"}, format="json"
        )

        assert response.status_code == 201
        ticket.refresh_from_db()
        assert ticket.status == SupportTicket.STATUS_OPEN
        assert Notification.objects.filter(user=agent, type="support_ticket").exists()

    def test_assignee_reply_flips_status_to_in_progress_and_notifies_requester(
        self, api_client, alice, agent
    ):
        ticket = SupportTicket.objects.create(requester=alice, assignee=agent, subject="q")
        api_client.force_authenticate(user=agent)

        response = api_client.post(
            f"/api/v1/support-tickets/{ticket.id}/messages/",
            {"body": "looking into it"},
            format="json",
        )

        assert response.status_code == 201
        ticket.refresh_from_db()
        assert ticket.status == SupportTicket.STATUS_IN_PROGRESS
        assert Notification.objects.filter(user=alice, type="support_ticket").exists()

    def test_assignee_can_view_and_reply(self, api_client, alice, agent):
        ticket = SupportTicket.objects.create(requester=alice, assignee=agent, subject="q")
        api_client.force_authenticate(user=agent)

        response = api_client.get(f"/api/v1/support-tickets/{ticket.id}/messages/")

        assert response.status_code == 200


class TestSlaBreach:
    def test_is_sla_breached_false_when_recent(self, alice):
        ticket = SupportTicket.objects.create(
            requester=alice, subject="q", priority=SupportTicket.PRIORITY_URGENT
        )
        assert ticket.is_sla_breached is False

    def test_is_sla_breached_false_once_resolved(self, alice):
        from datetime import timedelta

        from django.utils import timezone

        ticket = SupportTicket.objects.create(
            requester=alice,
            subject="q",
            priority=SupportTicket.PRIORITY_URGENT,
            status=SupportTicket.STATUS_RESOLVED,
        )
        SupportTicket.objects.filter(id=ticket.id).update(
            created_at=timezone.now() - timedelta(days=1)
        )
        ticket.refresh_from_db()

        assert ticket.is_sla_breached is False
