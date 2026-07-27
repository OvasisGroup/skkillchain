from unittest.mock import MagicMock

import pytest

from apps.audit.models import AuditLog
from apps.identity.models import OAuthIdentity
from apps.identity.oauth.base import OAuthUserInfo, OAuthVerificationError

pytestmark = pytest.mark.django_db


def _mock_provider(monkeypatch, info=None, error=None):
    provider = MagicMock()
    if error is not None:
        provider.verify.side_effect = error
    else:
        provider.verify.return_value = info
    monkeypatch.setattr("apps.identity.views.get_provider", lambda code: provider)
    return provider


def _oauth_login(api_client, provider="google"):
    return api_client.post(f"/api/v1/auth/oauth/{provider}/token/", {"token": "x"}, format="json")


class TestOAuthLogin:
    def test_unknown_provider_returns_404(self, api_client):
        response = _oauth_login(api_client, provider="unknown")

        assert response.status_code == 404

    def test_new_user_is_created_and_linked(self, api_client, monkeypatch):
        _mock_provider(
            monkeypatch,
            info=OAuthUserInfo(
                provider_user_id="g-1", email="newoauth@example.com", email_verified=True
            ),
        )

        response = _oauth_login(api_client)

        assert response.status_code == 200
        assert "access" in response.data
        identity = OAuthIdentity.objects.get(provider="google", provider_user_id="g-1")
        assert identity.user.email == "newoauth@example.com"
        assert AuditLog.objects.filter(action="user.oauth_register").exists()

    def test_existing_identity_logs_in_same_user_without_duplicating(
        self, api_client, monkeypatch, django_user_model
    ):
        user = django_user_model.objects.create_user(email="existing@example.com", password="x")
        OAuthIdentity.objects.create(user=user, provider="google", provider_user_id="g-2")
        _mock_provider(
            monkeypatch,
            info=OAuthUserInfo(
                provider_user_id="g-2", email="existing@example.com", email_verified=True
            ),
        )

        response = _oauth_login(api_client)

        assert response.status_code == 200
        assert OAuthIdentity.objects.filter(provider="google", provider_user_id="g-2").count() == 1
        assert AuditLog.objects.filter(action="user.oauth_login").exists()

    def test_links_to_existing_user_when_email_verified(
        self, api_client, monkeypatch, django_user_model
    ):
        user = django_user_model.objects.create_user(email="link-me@example.com", password="x")
        _mock_provider(
            monkeypatch,
            info=OAuthUserInfo(
                provider_user_id="g-3", email="link-me@example.com", email_verified=True
            ),
        )

        response = _oauth_login(api_client)

        assert response.status_code == 200
        identity = OAuthIdentity.objects.get(provider="google", provider_user_id="g-3")
        assert identity.user_id == user.id

    def test_refuses_to_link_unverified_email(self, api_client, monkeypatch, django_user_model):
        django_user_model.objects.create_user(email="taken@example.com", password="x")
        _mock_provider(
            monkeypatch,
            info=OAuthUserInfo(
                provider_user_id="g-4", email="taken@example.com", email_verified=False
            ),
        )

        response = _oauth_login(api_client)

        assert response.status_code == 401
        assert not OAuthIdentity.objects.filter(provider="google", provider_user_id="g-4").exists()

    def test_missing_email_and_no_existing_identity_rejected(self, api_client, monkeypatch):
        _mock_provider(
            monkeypatch, info=OAuthUserInfo(provider_user_id="g-5", email="", email_verified=False)
        )

        response = _oauth_login(api_client)

        assert response.status_code == 401

    def test_provider_verification_failure_returns_401(self, api_client, monkeypatch):
        _mock_provider(monkeypatch, error=OAuthVerificationError("bad token"))

        response = _oauth_login(api_client)

        assert response.status_code == 401
