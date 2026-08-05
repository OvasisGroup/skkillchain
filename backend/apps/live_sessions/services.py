from datetime import timedelta

from django.utils import timezone

from shared.crypto import decrypt, encrypt

from .conferencing.base import ConferencingProviderError
from .conferencing.registry import get_provider
from .models import ConferencingAccount

# Refresh a little before the real expiry rather than exactly at it, so a
# token that's valid when checked doesn't expire mid-flight during the
# provider API call that follows.
_EXPIRY_BUFFER = timedelta(seconds=60)


def get_valid_access_token(account: ConferencingAccount) -> str:
    """
    Returns a Google Meet/Zoom access token guaranteed not to be expired,
    refreshing and persisting a new one first if the stored token is stale
    or about to go stale — callers must not decrypt access_token_encrypted
    directly, since OAuth access tokens are short-lived (Google's expire in
    ~1 hour) and were previously used as-is forever, causing every meeting
    action to fail with a 401 once that hour passed.
    """
    if account.token_expires_at is None or account.token_expires_at > timezone.now() + _EXPIRY_BUFFER:
        return decrypt(account.access_token_encrypted)

    if not account.refresh_token_encrypted:
        raise ConferencingProviderError(
            f"{account.get_provider_display()} connection has expired and cannot be renewed "
            "automatically — reconnect the account."
        )

    provider_adapter = get_provider(account.provider)
    if provider_adapter is None:
        raise ConferencingProviderError(f"Unknown conferencing provider '{account.provider}'")

    tokens = provider_adapter.refresh_access_token(decrypt(account.refresh_token_encrypted))

    account.access_token_encrypted = encrypt(tokens.access_token)
    if tokens.refresh_token:
        account.refresh_token_encrypted = encrypt(tokens.refresh_token)
    account.token_expires_at = timezone.now() + timedelta(seconds=tokens.expires_in)
    account.save(update_fields=["access_token_encrypted", "refresh_token_encrypted", "token_expires_at"])

    return tokens.access_token
