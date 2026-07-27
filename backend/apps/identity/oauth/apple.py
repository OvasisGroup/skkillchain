import jwt
from django.conf import settings
from jwt import PyJWKClient

from .base import OAuthProvider, OAuthUserInfo, OAuthVerificationError

_JWKS_URL = "https://appleid.apple.com/auth/keys"
_ISSUER = "https://appleid.apple.com"


class AppleOAuthProvider(OAuthProvider):
    code = "apple"

    def __init__(self, jwks_client: PyJWKClient | None = None):
        # PyJWKClient caches fetched keys in-memory by default — injectable
        # here so tests can supply a fake client instead of hitting Apple.
        self._jwks_client = jwks_client

    def _get_jwks_client(self) -> PyJWKClient:
        if self._jwks_client is None:
            self._jwks_client = PyJWKClient(_JWKS_URL)
        return self._jwks_client

    def verify(self, token: str) -> OAuthUserInfo:
        try:
            signing_key = self._get_jwks_client().get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.APPLE_OAUTH_CLIENT_ID,
                issuer=_ISSUER,
            )
        except jwt.PyJWTError as exc:
            raise OAuthVerificationError(str(exc)) from exc

        return OAuthUserInfo(
            provider_user_id=claims["sub"],
            # Apple only includes email on the user's first authorization —
            # the OAuthLoginView handles a missing email on later logins by
            # falling back to the already-linked OAuthIdentity.
            email=claims.get("email", ""),
            email_verified=str(claims.get("email_verified", "false")).lower() == "true",
        )
