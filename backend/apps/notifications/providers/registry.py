from .base import NotificationProvider
from .email import EmailProvider
from .in_app import InAppProvider
from .push import PushProvider
from .sms import SmsProvider

_PROVIDERS: dict[str, type[NotificationProvider]] = {
    InAppProvider.code: InAppProvider,
    EmailProvider.code: EmailProvider,
    SmsProvider.code: SmsProvider,
    PushProvider.code: PushProvider,
}


def get_provider(channel: str) -> NotificationProvider | None:
    provider_class = _PROVIDERS.get(channel)
    if provider_class is None:
        return None
    return provider_class()
