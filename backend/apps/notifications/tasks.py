import logging

from celery import shared_task
from django.utils import timezone

from .models import Notification, NotificationTemplate
from .providers.registry import get_provider

logger = logging.getLogger(__name__)


def _render(notification: Notification, context: dict) -> tuple[str, str]:
    if not notification.template_code:
        return notification.title, notification.body

    template = (
        NotificationTemplate.objects.filter(
            code=notification.template_code, channel=notification.channel, is_active=True
        )
        .order_by("locale")
        .first()
    )
    if template is None:
        return notification.title, notification.body

    try:
        subject = template.subject_template.format(**context) if template.subject_template else ""
        body = template.body_template.format(**context)
    except (KeyError, IndexError):
        # A context key the template expects wasn't supplied — fall back to
        # the caller's defaults rather than failing the whole dispatch.
        logger.warning(
            "notifications.dispatch_notification: template %s missing a context key, "
            "using caller-supplied title/body instead",
            notification.template_code,
        )
        return notification.title, notification.body

    return subject or notification.title, body


@shared_task(name="notifications.dispatch_notification", time_limit=30)
def dispatch_notification(notification_id: str, context: dict | None = None) -> None:
    try:
        notification = Notification.objects.select_related("user").get(id=notification_id)
    except Notification.DoesNotExist:
        return

    provider = get_provider(notification.channel)
    if provider is None:
        logger.warning(
            "notifications.dispatch_notification: no provider registered for channel %s",
            notification.channel,
        )
        return

    title, body = _render(notification, context or {})
    provider.send(notification, title=title, body=body)

    notification.title = title
    notification.body = body
    notification.sent_at = timezone.now()
    notification.save(update_fields=["title", "body", "sent_at"])
