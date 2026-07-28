import logging

from .base import NotificationProvider

logger = logging.getLogger(__name__)


class PushProvider(NotificationProvider):
    """Same "no vendor named yet, log rather than fake it" stub as
    SmsProvider — see its docstring. Real push (e.g. FCM/APNs) is a
    provider-class swap away once a vendor is chosen."""

    code = "push"

    def send(self, notification, *, title: str, body: str) -> None:
        logger.info(
            "notifications.push (stub, no vendor configured): user=%s title=%s",
            notification.user_id,
            title,
        )
