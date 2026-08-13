import time
from unittest.mock import MagicMock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from apps.identity.oauth.apple import AppleOAuthProvider
from apps.identity.oauth.base import OAuthVerificationError
from apps.identity.oauth.facebook import FacebookOAuthProvider
from apps.identity.oauth.google import GoogleOAuthProvider


class TestGoogleOAuthProvider:
    def test_verify_returns_user_info(self, monkeypatch):
        monkeypatch.setattr(
            "apps.identity.oauth.google.google_id_token.verify_oauth2_token",
            lambda token, request, audience: {
                "iss": "accounts.google.com",
                "sub": "google-user-123",
                "email": "student@example.com",
                "email_verified": True,
            },
        )

        info = GoogleOAuthProvider().verify("fake-token")

        assert info.provider_user_id == "google-user-123"
        assert info.email == "student@example.com"
        assert info.email_verified is True

    def test_verify_rejects_wrong_issuer(self, monkeypatch):
        monkeypatch.setattr(
            "apps.identity.oauth.google.google_id_token.verify_oauth2_token",
            lambda token, request, audience: {
                "iss": "evil.example.com",
                "sub": "x",
                "email": "x@example.com",
            },
        )

        with pytest.raises(OAuthVerificationError):
            GoogleOAuthProvider().verify("fake-token")

    def test_verify_wraps_underlying_error(self, monkeypatch):
        def _raise(*args, **kwargs):
            raise ValueError("Token expired")

        monkeypatch.setattr(
            "apps.identity.oauth.google.google_id_token.verify_oauth2_token", _raise
        )

        with pytest.raises(OAuthVerificationError):
            GoogleOAuthProvider().verify("fake-token")


class TestFacebookOAuthProvider:
    """
    verify() now does two requests.get calls: /debug_token first (to confirm
    the token was actually issued for this app — see facebook.py), then /me.
    Fakes dispatch on the URL so both legs can be scripted independently.
    """

    def _debug_token_response(self, app_id="app-1", is_valid=True):
        class FakeResponse:
            status_code = 200

            def json(self):
                return {"data": {"is_valid": is_valid, "app_id": app_id}}

        return FakeResponse()

    def _me_response(self, status_code=200, body=None):
        class FakeResponse:
            def __init__(self):
                self.status_code = status_code

            def json(self):
                return body if body is not None else {}

        return FakeResponse()

    def _fake_get(self, debug_token_response=None, me_response=None):
        def fake_get(url, *args, **kwargs):
            if "debug_token" in url:
                return debug_token_response or self._debug_token_response()
            return me_response or self._me_response(200, {"id": "fb-user-1"})

        return fake_get

    def test_verify_returns_user_info(self, settings, monkeypatch):
        settings.FACEBOOK_APP_ID = "app-1"
        settings.FACEBOOK_APP_SECRET = "app-secret"
        monkeypatch.setattr(
            "apps.identity.oauth.facebook.requests.get",
            self._fake_get(me_response=self._me_response(200, {"id": "fb-user-1", "email": "fb@example.com"})),
        )

        info = FacebookOAuthProvider().verify("fake-token")

        assert info.provider_user_id == "fb-user-1"
        assert info.email == "fb@example.com"
        assert info.email_verified is True

    def test_verify_rejects_when_unconfigured(self, settings, monkeypatch):
        settings.FACEBOOK_APP_ID = ""
        settings.FACEBOOK_APP_SECRET = ""
        monkeypatch.setattr(
            "apps.identity.oauth.facebook.requests.get", self._fake_get()
        )

        with pytest.raises(OAuthVerificationError):
            FacebookOAuthProvider().verify("fake-token")

    def test_verify_rejects_token_issued_for_a_different_app(self, settings, monkeypatch):
        # The exact attack this check exists for: a token that's real and
        # valid, but was issued for someone else's Facebook app, not ours.
        settings.FACEBOOK_APP_ID = "app-1"
        settings.FACEBOOK_APP_SECRET = "app-secret"
        monkeypatch.setattr(
            "apps.identity.oauth.facebook.requests.get",
            self._fake_get(debug_token_response=self._debug_token_response(app_id="attacker-app")),
        )

        with pytest.raises(OAuthVerificationError):
            FacebookOAuthProvider().verify("fake-token")

    def test_verify_rejects_invalid_token(self, settings, monkeypatch):
        settings.FACEBOOK_APP_ID = "app-1"
        settings.FACEBOOK_APP_SECRET = "app-secret"
        monkeypatch.setattr(
            "apps.identity.oauth.facebook.requests.get",
            self._fake_get(debug_token_response=self._debug_token_response(is_valid=False)),
        )

        with pytest.raises(OAuthVerificationError):
            FacebookOAuthProvider().verify("fake-token")

    def test_verify_rejects_bad_status(self, settings, monkeypatch):
        settings.FACEBOOK_APP_ID = "app-1"
        settings.FACEBOOK_APP_SECRET = "app-secret"
        monkeypatch.setattr(
            "apps.identity.oauth.facebook.requests.get",
            self._fake_get(me_response=self._me_response(400, {})),
        )

        with pytest.raises(OAuthVerificationError):
            FacebookOAuthProvider().verify("fake-token")

    def test_verify_rejects_response_without_id(self, settings, monkeypatch):
        settings.FACEBOOK_APP_ID = "app-1"
        settings.FACEBOOK_APP_SECRET = "app-secret"
        monkeypatch.setattr(
            "apps.identity.oauth.facebook.requests.get",
            self._fake_get(me_response=self._me_response(200, {"email": "no-id@example.com"})),
        )

        with pytest.raises(OAuthVerificationError):
            FacebookOAuthProvider().verify("fake-token")


class TestAppleOAuthProvider:
    """
    Exercises the real RS256 verification path with a genuinely signed JWT
    (generated with a throwaway RSA keypair) rather than mocking jwt.decode
    itself — only the JWKS *fetch* is faked, so the signature/issuer/
    audience/expiry checks are the real ones from PyJWT.
    """

    def _keypair(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        return private_key, private_key.public_key()

    def _token(self, private_key, **claims):
        return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test-kid"})

    def _fake_jwks_client(self, public_key):
        signing_key = MagicMock()
        signing_key.key = public_key
        client = MagicMock()
        client.get_signing_key_from_jwt.return_value = signing_key
        return client

    def test_verify_accepts_genuinely_signed_token(self, settings):
        settings.APPLE_OAUTH_CLIENT_ID = "com.skillchain.app"
        private_key, public_key = self._keypair()
        now = int(time.time())
        token = self._token(
            private_key,
            iss="https://appleid.apple.com",
            aud="com.skillchain.app",
            sub="apple-user-1",
            email="apple@example.com",
            email_verified="true",
            iat=now,
            exp=now + 300,
        )

        info = AppleOAuthProvider(jwks_client=self._fake_jwks_client(public_key)).verify(token)

        assert info.provider_user_id == "apple-user-1"
        assert info.email == "apple@example.com"
        assert info.email_verified is True

    def test_verify_rejects_wrong_audience(self, settings):
        settings.APPLE_OAUTH_CLIENT_ID = "com.skillchain.app"
        private_key, public_key = self._keypair()
        now = int(time.time())
        token = self._token(
            private_key,
            iss="https://appleid.apple.com",
            aud="some-other-app",
            sub="apple-user-1",
            iat=now,
            exp=now + 300,
        )

        with pytest.raises(OAuthVerificationError):
            AppleOAuthProvider(jwks_client=self._fake_jwks_client(public_key)).verify(token)

    def test_verify_rejects_expired_token(self, settings):
        settings.APPLE_OAUTH_CLIENT_ID = "com.skillchain.app"
        private_key, public_key = self._keypair()
        now = int(time.time())
        token = self._token(
            private_key,
            iss="https://appleid.apple.com",
            aud="com.skillchain.app",
            sub="apple-user-1",
            iat=now - 1000,
            exp=now - 500,
        )

        with pytest.raises(OAuthVerificationError):
            AppleOAuthProvider(jwks_client=self._fake_jwks_client(public_key)).verify(token)

    def test_verify_rejects_wrong_issuer(self, settings):
        settings.APPLE_OAUTH_CLIENT_ID = "com.skillchain.app"
        private_key, public_key = self._keypair()
        now = int(time.time())
        token = self._token(
            private_key,
            iss="https://evil.example.com",
            aud="com.skillchain.app",
            sub="apple-user-1",
            iat=now,
            exp=now + 300,
        )

        with pytest.raises(OAuthVerificationError):
            AppleOAuthProvider(jwks_client=self._fake_jwks_client(public_key)).verify(token)
