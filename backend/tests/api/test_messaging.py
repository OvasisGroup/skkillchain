import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import RefreshToken

from apps.messaging.models import Message, Thread, ThreadParticipant
from config.asgi import application

pytestmark = pytest.mark.django_db


def _access_token(user) -> str:
    return str(RefreshToken.for_user(user).access_token)


_async_access_token = database_sync_to_async(_access_token)


@pytest.fixture
def alice(django_user_model):
    return django_user_model.objects.create_user(email="alice@example.com", password="x")


@pytest.fixture
def bob(django_user_model):
    return django_user_model.objects.create_user(email="bob@example.com", password="x")


@pytest.fixture
def eve(django_user_model):
    # Not a participant of anything below — used for the negative WS test.
    return django_user_model.objects.create_user(email="eve@example.com", password="x")


@pytest.fixture
def alice_client(api_client, alice):
    api_client.force_authenticate(user=alice)
    return api_client


class TestThreadsAndMessagesRest:
    def test_create_thread_adds_creator_and_participants(self, alice_client, alice, bob):
        response = alice_client.post(
            "/api/v1/threads/", {"participant_ids": [str(bob.id)]}, format="json"
        )

        assert response.status_code == 201
        assert set(response.data["participant_ids"]) == {str(alice.id), str(bob.id)}

    def test_list_threads_only_shows_own_threads(self, alice_client, alice, bob, eve):
        thread = Thread.objects.create(created_by=alice, thread_type=Thread.TYPE_DIRECT)
        ThreadParticipant.objects.bulk_create(
            [
                ThreadParticipant(thread=thread, user=alice),
                ThreadParticipant(thread=thread, user=bob),
            ]
        )
        other_thread = Thread.objects.create(created_by=bob, thread_type=Thread.TYPE_DIRECT)
        ThreadParticipant.objects.create(thread=other_thread, user=bob)

        response = alice_client.get("/api/v1/threads/")

        ids = [t["id"] for t in response.data["results"]]
        assert str(thread.id) in ids
        assert str(other_thread.id) not in ids

    def test_post_message_creates_it_in_thread(self, alice_client, alice, bob):
        thread = Thread.objects.create(created_by=alice, thread_type=Thread.TYPE_DIRECT)
        ThreadParticipant.objects.bulk_create(
            [
                ThreadParticipant(thread=thread, user=alice),
                ThreadParticipant(thread=thread, user=bob),
            ]
        )

        response = alice_client.post(
            f"/api/v1/threads/{thread.id}/messages/", {"body": "hi bob"}, format="json"
        )

        assert response.status_code == 201
        assert Message.objects.filter(thread=thread, body="hi bob").exists()

    def test_non_participant_cannot_read_thread_messages(self, alice_client, alice, bob, eve):
        thread = Thread.objects.create(created_by=alice, thread_type=Thread.TYPE_DIRECT)
        ThreadParticipant.objects.create(thread=thread, user=alice)

        eve_client_response = alice_client
        eve_client_response.force_authenticate(user=eve)
        response = eve_client_response.get(f"/api/v1/threads/{thread.id}/messages/")

        assert response.status_code == 403


class TestChatWebsocket:
    @database_sync_to_async
    def _make_thread(self, alice, bob):
        thread = Thread.objects.create(created_by=alice, thread_type=Thread.TYPE_DIRECT)
        ThreadParticipant.objects.bulk_create(
            [
                ThreadParticipant(thread=thread, user=alice),
                ThreadParticipant(thread=thread, user=bob),
            ]
        )
        return thread

    @pytest.mark.django_db(transaction=True)
    async def test_message_sent_by_one_connection_is_delivered_to_another(self, alice, bob):
        thread = await self._make_thread(alice, bob)
        path = f"/ws/chat/{thread.id}/"

        alice_token = await _async_access_token(alice)
        bob_token = await _async_access_token(bob)
        alice_ws = WebsocketCommunicator(application, f"{path}?token={alice_token}")
        bob_ws = WebsocketCommunicator(application, f"{path}?token={bob_token}")
        try:
            connected, _ = await alice_ws.connect()
            assert connected
            connected, _ = await bob_ws.connect()
            assert connected

            await alice_ws.send_json_to({"body": "hello bob"})

            delivered = await bob_ws.receive_json_from(timeout=5)
            assert delivered["body"] == "hello bob"
            assert delivered["sender_id"] == str(alice.id)
        finally:
            await alice_ws.disconnect()
            await bob_ws.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_non_participant_cannot_join_thread(self, alice, bob, eve):
        thread = await self._make_thread(alice, bob)
        path = f"/ws/chat/{thread.id}/"

        eve_token = await _async_access_token(eve)
        eve_ws = WebsocketCommunicator(application, f"{path}?token={eve_token}")
        connected, _ = await eve_ws.connect()

        assert connected is False
        await eve_ws.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_unauthenticated_connection_is_rejected(self, alice, bob):
        thread = await self._make_thread(alice, bob)
        path = f"/ws/chat/{thread.id}/"

        anon_ws = WebsocketCommunicator(application, path)
        connected, _ = await anon_ws.connect()

        assert connected is False
        await anon_ws.disconnect()
