import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.core import mail
from rest_framework_simplejwt.tokens import RefreshToken

from apps.notifications import tasks
from apps.notifications.models import EmailTemplate, Notification, NotificationTemplate
from apps.notifications.services import notify
from config.asgi import application

pytestmark = pytest.mark.django_db


@pytest.fixture
def alice(django_user_model):
    return django_user_model.objects.create_user(email="alice@example.com", password="x")


@pytest.fixture
def bob(django_user_model):
    return django_user_model.objects.create_user(email="bob@example.com", password="x")


@pytest.fixture
def alice_client(api_client, alice):
    api_client.force_authenticate(user=alice)
    return api_client


class TestNotifyService:
    def test_notify_creates_one_row_per_channel(self, alice):
        notifications = notify(
            alice, type="system", channels=["in_app", "email"], title="Hi", body="Hello"
        )

        assert len(notifications) == 2
        assert {n.channel for n in notifications} == {"in_app", "email"}
        assert Notification.objects.filter(user=alice).count() == 2


class TestDispatchNotificationTask:
    def test_dispatch_without_template_uses_caller_supplied_title_and_body(self, alice):
        notification = Notification.objects.create(
            user=alice, type="system", channel="email", title="Hi", body="Hello"
        )

        tasks.dispatch_notification(str(notification.id), {})

        notification.refresh_from_db()
        assert notification.sent_at is not None
        assert len(mail.outbox) == 1
        assert mail.outbox[0].body == "Hello"
        assert mail.outbox[0].to == [alice.email]

    def test_dispatch_renders_active_template_with_context(self, alice):
        NotificationTemplate.objects.create(
            code="welcome",
            channel="email",
            subject_template="Hi {name}",
            body_template="Welcome, {name}!",
        )
        notification = Notification.objects.create(
            user=alice, type="system", channel="email", template_code="welcome"
        )

        tasks.dispatch_notification(str(notification.id), {"name": "Alice"})

        notification.refresh_from_db()
        assert notification.title == "Hi Alice"
        assert notification.body == "Welcome, Alice!"
        assert mail.outbox[0].body == "Welcome, Alice!"

    def test_dispatch_falls_back_when_context_missing_placeholder(self, alice):
        NotificationTemplate.objects.create(
            code="welcome", channel="email", body_template="Welcome, {name}!"
        )
        notification = Notification.objects.create(
            user=alice,
            type="system",
            channel="email",
            template_code="welcome",
            title="fallback title",
            body="fallback body",
        )

        tasks.dispatch_notification(str(notification.id), {})

        notification.refresh_from_db()
        assert notification.body == "fallback body"

    def test_email_provider_uses_email_template_html_body(self, alice):
        EmailTemplate.objects.create(
            code="welcome", subject="Welcome", html_body="<p>hi</p>", text_body="hi"
        )
        notification = Notification.objects.create(
            user=alice, type="system", channel="email", template_code="welcome", body="hi"
        )

        tasks.dispatch_notification(str(notification.id), {})

        assert mail.outbox[0].alternatives == [("<p>hi</p>", "text/html")]

    def test_unknown_notification_id_is_a_noop(self):
        tasks.dispatch_notification("00000000-0000-0000-0000-000000000000", {})


class TestNotificationsRest:
    def test_list_only_returns_own_notifications(self, alice_client, alice, bob):
        Notification.objects.create(user=alice, type="system", channel="in_app", title="mine")
        Notification.objects.create(user=bob, type="system", channel="in_app", title="not mine")

        response = alice_client.get("/api/v1/notifications/")

        titles = [n["title"] for n in response.data["results"]]
        assert titles == ["mine"]

    def test_mark_read_marks_specified_ids(self, alice_client, alice):
        n1 = Notification.objects.create(user=alice, type="system", channel="in_app")
        n2 = Notification.objects.create(user=alice, type="system", channel="in_app")

        response = alice_client.post(
            "/api/v1/notifications/mark-read/", {"notification_ids": [str(n1.id)]}, format="json"
        )

        assert response.data == {"marked_read": 1}
        n1.refresh_from_db()
        n2.refresh_from_db()
        assert n1.read_at is not None
        assert n2.read_at is None

    def test_mark_read_without_ids_marks_all_unread(self, alice_client, alice):
        Notification.objects.create(user=alice, type="system", channel="in_app")
        Notification.objects.create(user=alice, type="system", channel="in_app")

        response = alice_client.post("/api/v1/notifications/mark-read/", {}, format="json")

        assert response.data == {"marked_read": 2}


class TestNotificationsWebsocket:
    @pytest.mark.django_db(transaction=True)
    async def test_in_app_notification_is_pushed_live(self, alice):
        token = await database_sync_to_async(
            lambda: str(RefreshToken.for_user(alice).access_token)
        )()
        ws = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
        try:
            connected, _ = await ws.connect()
            assert connected

            notification = await database_sync_to_async(Notification.objects.create)(
                user=alice, type="system", channel="in_app", title="Hi", body="Hello"
            )
            await database_sync_to_async(tasks.dispatch_notification)(str(notification.id), {})

            pushed = await ws.receive_json_from(timeout=5)
            assert pushed["title"] == "Hi"
            assert pushed["body"] == "Hello"
        finally:
            await ws.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_unauthenticated_connection_is_rejected(self):
        ws = WebsocketCommunicator(application, "/ws/notifications/")
        connected, _ = await ws.connect()

        assert connected is False
        await ws.disconnect()
