from dataclasses import dataclass


@dataclass
class OAuthUserInfo:
    provider_user_id: str
    email: str
    email_verified: bool


class OAuthVerificationError(Exception):
    """Raised whenever a provider token fails verification for any reason —
    the view maps this to a 401, never a 500, since an invalid/expired
    client-supplied token is an expected failure mode, not a server bug."""


class OAuthProvider:
    code: str = ""

    def verify(self, token: str) -> OAuthUserInfo:
        raise NotImplementedError
