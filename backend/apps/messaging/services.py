from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from .models import Message, Thread, ThreadParticipant


def create_thread(creator, *, participant_ids, thread_type=Thread.TYPE_DIRECT, subject=""):
    with transaction.atomic():
        thread = Thread.objects.create(
            created_by=creator, thread_type=thread_type, subject=subject
        )
        participant_user_ids = set(participant_ids) | {creator.id}
        ThreadParticipant.objects.bulk_create(
            [
                ThreadParticipant(thread=thread, user_id=user_id)
                for user_id in participant_user_ids
            ]
        )
    return thread


def create_message(thread: Thread, sender, body: str, metadata: dict | None = None) -> Message:
    message = Message.objects.create(
        thread=thread, sender=sender, body=body, metadata=metadata or {}
    )
    _broadcast_message(message)
    return message


def _broadcast_message(message: Message) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"thread_{message.thread_id}",
        {
            "type": "chat.message",
            "message": {
                "id": str(message.id),
                "thread_id": str(message.thread_id),
                "sender_id": str(message.sender_id),
                "body": message.body,
                "metadata": message.metadata,
                "created_at": message.created_at.isoformat(),
            },
        },
    )
