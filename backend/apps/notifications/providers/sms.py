import logging

from .base import NotificationProvider

logger = logging.getLogger(__name__)


class SmsProvider(NotificationProvider):
    """
    No SMS vendor (e.g. Twilio) is named anywhere in the SRS/product docs,
    unlike the payment/conferencing providers, which each have a documented
    required integration (Stripe/PayPal/M-Pesa, Zoom/Google Meet). Rather
    than picking a vendor with no requirement behind it, or silently
    pretending a send succeeded, this logs what would have gone out —
    same precedent as apps/live_sessions/tasks.py's dispatch_reminders
    before this milestone. Swapping in a real vendor later is a change to
    this one class, not to anything that calls notify().
    """

    code = "sms"

    def send(self, notification, *, title: str, body: str) -> None:
        logger.info(
            "notifications.sms (stub, no vendor configured): user=%s body=%s",
            notification.user_id,
            body,
        )
