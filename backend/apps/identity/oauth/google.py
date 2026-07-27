from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from .base import OAuthProvider, OAuthUserInfo, OAuthVerificationError

_VALID_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


class GoogleOAuthProvider(OAuthProvider):
    code = "google"

    def verify(self, token: str) -> OAuthUserInfo:
        try:
            claims = google_id_token.verify_oauth2_token(
                token, google_requests.Request(), audience=settings.GOOGLE_OAUTH_CLIENT_ID
            )
        except ValueError as exc:
            raise OAuthVerificationError(str(exc)) from exc

        if claims.get("iss") not in _VALID_ISSUERS:
            raise OAuthVerificationError("Unexpected token issuer")

        return OAuthUserInfo(
            provider_user_id=claims["sub"],
            email=claims.get("email", ""),
            email_verified=bool(claims.get("email_verified", False)),
        )
