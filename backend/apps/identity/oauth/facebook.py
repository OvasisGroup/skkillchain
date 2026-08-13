import requests
from django.conf import settings

from .base import OAuthProvider, OAuthUserInfo, OAuthVerificationError

_GRAPH_ME_URL = "https://graph.facebook.com/v19.0/me"
_DEBUG_TOKEN_URL = "https://graph.facebook.com/v19.0/debug_token"


class FacebookOAuthProvider(OAuthProvider):
    code = "facebook"

    def verify(self, token: str) -> OAuthUserInfo:
        self._verify_app_id(token)

        try:
            response = requests.get(
                _GRAPH_ME_URL, params={"fields": "id,email", "access_token": token}, timeout=5
            )
        except requests.RequestException as exc:
            raise OAuthVerificationError(f"Could not reach Facebook: {exc}") from exc

        if response.status_code != 200:
            raise OAuthVerificationError("Facebook rejected the provided token")

        data = response.json()
        if "id" not in data:
            raise OAuthVerificationError("Facebook response did not include a user id")

        return OAuthUserInfo(
            provider_user_id=data["id"],
            email=data.get("email", ""),
            # Facebook's /me doesn't expose an email_verified flag; an email
            # present in the response has already been verified by Facebook
            # itself (it doesn't return unverified emails here).
            email_verified=bool(data.get("email")),
        )

    def _verify_app_id(self, token: str) -> None:
        # Facebook access tokens are valid across every app a user has
        # authorized, not just ours — a token minted for a completely
        # unrelated (attacker-controlled) Facebook app still carries the
        # user's real Facebook identity. Without checking /debug_token's
        # app_id, that token would be accepted here as if it proved the
        # user authenticated with *this* app, allowing account takeover of
        # any SkillChain account already linked to that Facebook id.
        if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
            raise OAuthVerificationError("Facebook login is not configured")

        app_access_token = f"{settings.FACEBOOK_APP_ID}|{settings.FACEBOOK_APP_SECRET}"
        try:
            response = requests.get(
                _DEBUG_TOKEN_URL,
                params={"input_token": token, "access_token": app_access_token},
                timeout=5,
            )
        except requests.RequestException as exc:
            raise OAuthVerificationError(f"Could not reach Facebook: {exc}") from exc

        if response.status_code != 200:
            raise OAuthVerificationError("Facebook rejected the provided token")

        data = response.json().get("data", {})
        if not data.get("is_valid"):
            raise OAuthVerificationError("Facebook token is not valid")
        if str(data.get("app_id")) != str(settings.FACEBOOK_APP_ID):
            raise OAuthVerificationError("Facebook token was not issued for this app")
