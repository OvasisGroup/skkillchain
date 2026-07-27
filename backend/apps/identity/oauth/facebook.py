import requests

from .base import OAuthProvider, OAuthUserInfo, OAuthVerificationError

_GRAPH_ME_URL = "https://graph.facebook.com/v19.0/me"


class FacebookOAuthProvider(OAuthProvider):
    code = "facebook"

    def verify(self, token: str) -> OAuthUserInfo:
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
