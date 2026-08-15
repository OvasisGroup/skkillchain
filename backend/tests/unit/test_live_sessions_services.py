from datetime import timedelta

import pytest
from django.utils import timezone

from apps.live_sessions.conferencing.base import ConferencingProviderError
from apps.live_sessions.models import ConferencingAccount
from apps.live_sessions.services import get_valid_access_token
from shared.crypto import decrypt, encrypt

pytestmark = pytest.mark.django_db


class _FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = str(payload)

    def json(self):
        return self._payload


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


class TestGetValidAccessToken:
    def test_returns_stored_token_unchanged_when_not_expired(self, user):
        account = ConferencingAccount.objects.create(
            user=user,
            provider=ConferencingAccount.PROVIDER_ZOOM,
            access_token_encrypted=encrypt("still-good"),
            refresh_token_encrypted=encrypt("some-refresh-token"),
            token_expires_at=timezone.now() + timedelta(hours=1),
        )

        token = get_valid_access_token(account)

        assert token == "still-good"

    def test_refreshes_and_persists_when_expired(self, user, monkeypatch):
        account = ConferencingAccount.objects.create(
            user=user,
            provider=ConferencingAccount.PROVIDER_ZOOM,
            access_token_encrypted=encrypt("stale-token"),
            refresh_token_encrypted=encrypt("valid-refresh-token"),
            # Already past — this is exactly the "1 hour later" state that
            # every meeting action used to hit a bare 401 on.
            token_expires_at=timezone.now() - timedelta(minutes=5),
        )
        monkeypatch.setattr(
            "apps.live_sessions.conferencing.zoom.requests.post",
            lambda *a, **k: _FakeResponse(
                200,
                {"access_token": "fresh-token", "refresh_token": "rotated-rt", "expires_in": 3600},
            ),
        )

        token = get_valid_access_token(account)

        assert token == "fresh-token"
        account.refresh_from_db()
        assert decrypt(account.access_token_encrypted) == "fresh-token"
        assert decrypt(account.refresh_token_encrypted) == "rotated-rt"
        assert account.token_expires_at > timezone.now() + timedelta(minutes=59)

    def test_refresh_failure_raises_clear_error_and_leaves_account_untouched(
        self, user, monkeypatch
    ):
        account = ConferencingAccount.objects.create(
            user=user,
            provider=ConferencingAccount.PROVIDER_GOOGLE_MEET,
            access_token_encrypted=encrypt("stale-token"),
            refresh_token_encrypted=encrypt("revoked-refresh-token"),
            token_expires_at=timezone.now() - timedelta(minutes=5),
        )
        monkeypatch.setattr(
            "apps.live_sessions.conferencing.google_meet.requests.post",
            lambda *a, **k: _FakeResponse(400, {"error": "invalid_grant"}),
        )

        with pytest.raises(ConferencingProviderError):
            get_valid_access_token(account)

        account.refresh_from_db()
        assert decrypt(account.access_token_encrypted) == "stale-token"

    def test_expired_with_no_refresh_token_raises_reconnect_error(self, user):
        account = ConferencingAccount.objects.create(
            user=user,
            provider=ConferencingAccount.PROVIDER_GOOGLE_MEET,
            access_token_encrypted=encrypt("stale-token"),
            refresh_token_encrypted="",
            token_expires_at=timezone.now() - timedelta(minutes=5),
        )

        with pytest.raises(ConferencingProviderError, match="reconnect"):
            get_valid_access_token(account)
