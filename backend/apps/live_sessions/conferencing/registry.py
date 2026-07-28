from .base import ConferencingProvider
from .google_meet import GoogleMeetConferencingProvider
from .zoom import ZoomConferencingProvider

_PROVIDERS: dict[str, type[ConferencingProvider]] = {
    ZoomConferencingProvider.code: ZoomConferencingProvider,
    GoogleMeetConferencingProvider.code: GoogleMeetConferencingProvider,
}


def get_provider(code: str) -> ConferencingProvider | None:
    provider_class = _PROVIDERS.get(code)
    if provider_class is None:
        return None
    return provider_class()
