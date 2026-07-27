from .apple import AppleOAuthProvider
from .base import OAuthProvider
from .facebook import FacebookOAuthProvider
from .google import GoogleOAuthProvider

_PROVIDERS: dict[str, type[OAuthProvider]] = {
    GoogleOAuthProvider.code: GoogleOAuthProvider,
    AppleOAuthProvider.code: AppleOAuthProvider,
    FacebookOAuthProvider.code: FacebookOAuthProvider,
}


def get_provider(code: str) -> OAuthProvider | None:
    provider_class = _PROVIDERS.get(code)
    if provider_class is None:
        return None
    return provider_class()
