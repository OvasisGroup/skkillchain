from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.learning.models import Enrollment

from . import services


class DiscussionConsumer(AsyncJsonWebsocketConsumer):
    """ws/course/{course_id}/discussion/ — any enrolled student (any
    status, unlike reviews' completed-only gate) can join and post."""

    async def connect(self):
        self.course_id = self.scope["url_route"]["kwargs"]["course_id"]
        user = self.scope["user"]
        if not user.is_authenticated or not await self._is_enrolled(user):
            await self.close(code=4003)
            return
        self.group_name = f"course_{self.course_id}_discussion"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        body = (content.get("body") or "").strip()
        if not body:
            return
        await self._create_post(self.scope["user"], body)

    async def discussion_post(self, event):
        await self.send_json(event["post"])

    @database_sync_to_async
    def _is_enrolled(self, user) -> bool:
        return Enrollment.objects.filter(course_id=self.course_id, student=user).exists()

    @database_sync_to_async
    def _create_post(self, user, body: str) -> None:
        from apps.catalog.models import Course

        course = Course.objects.get(id=self.course_id)
        services.create_discussion_post(course, user, body)
