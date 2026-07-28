from .models import Notification


def notify(
    user,
    *,
    type: str,
    channels: list[str],
    template_code: str = "",
    title: str = "",
    body: str = "",
    context: dict | None = None,
) -> list[Notification]:
    """Creates one Notification row per requested channel (a row's channel
    is fixed at creation, per the notifications table's own schema — that's
    what a multi-channel fan-out means here) and queues each for async
    dispatch. Never called inline in a request/task path expecting an
    immediate send; the Celery task is what actually renders the template
    and hits the provider."""
    from . import tasks

    notifications = []
    for channel in channels:
        notification = Notification.objects.create(
            user=user,
            type=type,
            channel=channel,
            template_code=template_code,
            title=title,
            body=body,
        )
        notifications.append(notification)
        tasks.dispatch_notification.delay(str(notification.id), context or {})
    return notifications
