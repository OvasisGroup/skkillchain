from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from . import services
from .models import Thread


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    ws/chat/{thread_id}/ — a connection joins the channel-layer group for
    that thread only after confirming the authenticated user is actually a
    ThreadParticipant (the security-checklist negative test: a user must
    not be able to subscribe to another user's thread). REST POST and a WS
    "send" both go through services.create_message, so either path
    broadcasts to the same group.
    """

    async def connect(self):
        self.thread_id = self.scope["url_route"]["kwargs"]["thread_id"]
        user = self.scope["user"]
        if not user.is_authenticated or not await self._is_participant(user):
            await self.close(code=4003)
            return
        self.group_name = f"thread_{self.thread_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        body = (content.get("body") or "").strip()
        if not body:
            return
        await self._create_message(self.scope["user"], body)

    async def chat_message(self, event):
        await self.send_json(event["message"])

    @database_sync_to_async
    def _is_participant(self, user) -> bool:
        return Thread.objects.filter(id=self.thread_id, participants__user=user).exists()

    @database_sync_to_async
    def _create_message(self, user, body: str) -> None:
        thread = Thread.objects.get(id=self.thread_id)
        services.create_message(thread, user, body)
