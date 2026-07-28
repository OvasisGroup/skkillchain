from django.core import signing

_SALT = "live_sessions.conferencing-oauth-state"
# Long enough for the user to complete the provider's consent screen.
_MAX_AGE_SECONDS = 600


def issue_state(user_id, provider: str) -> str:
    return signing.dumps({"user_id": str(user_id), "provider": provider}, salt=_SALT)


def resolve_state(state: str) -> dict | None:
    try:
        return signing.loads(state, salt=_SALT, max_age=_MAX_AGE_SECONDS)
    except signing.BadSignature:
        return None
