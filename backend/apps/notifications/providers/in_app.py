from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .base import NotificationProvider


class InAppProvider(NotificationProvider):
    """Pushes over the ws/notifications/ channel to whichever of the
    user's connections are currently open — the Notification row itself is
    already the durable copy (that's what GET /notifications reads), this
    is just the live-delivery half of it."""

    code = "in_app"

    def send(self, notification, *, title: str, body: str) -> None:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        async_to_sync(channel_layer.group_send)(
            f"user_{notification.user_id}_notifications",
            {
                "type": "notification.push",
                "notification": {
                    "id": str(notification.id),
                    "type": notification.type,
                    "title": title,
                    "body": body,
                    "created_at": notification.created_at.isoformat(),
                },
            },
        )
