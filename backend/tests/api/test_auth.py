import base64

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.audit.models import AuditLog
from apps.identity.models import Profile

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "a-strong-password-1"

# Smallest possible valid PNG (1x1 transparent pixel) — real image bytes are
# required since ImageField validation actually decodes the file via Pillow.
_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _register(api_client, email="new@example.com", password=STRONG_PASSWORD):
    return api_client.post(
        "/api/v1/auth/register/", {"email": email, "password": password}, format="json"
    )


def _login(api_client, email, password=STRONG_PASSWORD):
    return api_client.post(
        "/api/v1/auth/login/", {"email": email, "password": password}, format="json"
    )


class TestRegister:
    def test_register_creates_user_and_profile(self, api_client):
        response = _register(api_client)

        assert response.status_code == 201
        assert response.data["email"] == "new@example.com"
        assert "profile" in response.data
        assert Profile.objects.filter(user__email="new@example.com").exists()
        assert AuditLog.objects.filter(action="user.register").exists()

    def test_register_duplicate_email_rejected(self, api_client):
        _register(api_client)
        response = _register(api_client)

        assert response.status_code == 400

    def test_register_weak_password_rejected(self, api_client):
        response = _register(api_client, password="short")

        assert response.status_code == 400
        # RFC 7807 shape (docs/03-api/01-api-documentation.md §17).
        assert response["Content-Type"] == "application/problem+json"
        assert response.data["status"] == 400
        assert "type" in response.data
        assert "errors" in response.data


class TestLogin:
    def test_login_returns_tokens_and_audit_logs(self, api_client):
        _register(api_client, email="login@example.com")

        response = _login(api_client, "login@example.com")

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        assert AuditLog.objects.filter(action="user.login").exists()

    def test_login_wrong_password_rejected(self, api_client):
        _register(api_client, email="login2@example.com")

        response = _login(api_client, "login2@example.com", password="wrong-password")

        assert response.status_code == 401


class TestMe:
    def test_me_requires_authentication(self, api_client):
        response = api_client.get("/api/v1/auth/me/")

        assert response.status_code == 401

    def test_me_returns_profile_when_authenticated(self, api_client):
        _register(api_client, email="me@example.com")
        login = _login(api_client, "me@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = api_client.get("/api/v1/auth/me/")

        assert response.status_code == 200
        assert response.data["email"] == "me@example.com"

    def test_me_patch_updates_profile(self, api_client):
        _register(api_client, email="patch@example.com")
        login = _login(api_client, "patch@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = api_client.patch(
            "/api/v1/auth/me/", {"profile": {"first_name": "Ada"}}, format="json"
        )

        assert response.status_code == 200
        assert response.data["profile"]["first_name"] == "Ada"

    def test_me_patch_updates_social_links(self, api_client):
        _register(api_client, email="social@example.com")
        login = _login(api_client, "social@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = api_client.patch(
            "/api/v1/auth/me/",
            {
                "profile": {
                    "linkedin_url": "https://linkedin.com/in/ada",
                    "twitter_url": "https://twitter.com/ada",
                    "github_url": "https://github.com/ada",
                    "youtube_url": "https://youtube.com/@ada",
                    "website_url": "https://ada.dev",
                }
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["profile"]["linkedin_url"] == "https://linkedin.com/in/ada"
        assert response.data["profile"]["github_url"] == "https://github.com/ada"
        assert response.data["profile"]["youtube_url"] == "https://youtube.com/@ada"

    def test_me_patch_updates_bio(self, api_client):
        _register(api_client, email="bio@example.com")
        login = _login(api_client, "bio@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = api_client.patch(
            "/api/v1/auth/me/",
            {"profile": {"bio": "Backend engineer turned Django instructor."}},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["profile"]["bio"] == "Backend engineer turned Django instructor."

    def test_me_patch_cannot_set_avatar_directly(self, api_client):
        # avatar is read-only on this JSON endpoint — a file can't travel
        # through a plain PATCH body, so a string value is just ignored
        # rather than erroring, and the dedicated upload endpoint is used
        # instead (see TestAvatarUpload below).
        _register(api_client, email="noavatar@example.com")
        login = _login(api_client, "noavatar@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = api_client.patch(
            "/api/v1/auth/me/",
            {"profile": {"avatar": "https://evil.example.com/x.png"}},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["profile"]["avatar"] in (None, "")


class TestAvatarUpload:
    def test_uploads_avatar(self, api_client, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path  # keep the uploaded test file out of the real media/ dir
        _register(api_client, email="avatar@example.com")
        login = _login(api_client, "avatar@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        image = SimpleUploadedFile("avatar.png", _ONE_PIXEL_PNG, content_type="image/png")

        response = api_client.post("/api/v1/auth/me/avatar/", {"avatar": image}, format="multipart")

        assert response.status_code == 200
        assert response.data["profile"]["avatar"]
        profile = Profile.objects.get(user__email="avatar@example.com")
        assert profile.avatar.name

    def test_requires_authentication(self, api_client, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        image = SimpleUploadedFile("avatar.png", _ONE_PIXEL_PNG, content_type="image/png")

        response = api_client.post("/api/v1/auth/me/avatar/", {"avatar": image}, format="multipart")

        assert response.status_code == 401

    def test_rejects_non_image_file(self, api_client, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        _register(api_client, email="badavatar@example.com")
        login = _login(api_client, "badavatar@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        not_an_image = SimpleUploadedFile("avatar.txt", b"not an image", content_type="text/plain")

        response = api_client.post(
            "/api/v1/auth/me/avatar/", {"avatar": not_an_image}, format="multipart"
        )

        assert response.status_code == 400

    def test_me_patch_updates_email(self, api_client):
        _register(api_client, email="oldmail@example.com")
        login = _login(api_client, "oldmail@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = api_client.patch(
            "/api/v1/auth/me/", {"email": "newmail@example.com"}, format="json"
        )

        assert response.status_code == 200
        assert response.data["email"] == "newmail@example.com"

    def test_me_patch_email_rejects_existing_address(self, api_client):
        _register(api_client, email="taken@example.com")
        _register(api_client, email="mine@example.com")
        login = _login(api_client, "mine@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = api_client.patch(
            "/api/v1/auth/me/", {"email": "taken@example.com"}, format="json"
        )

        assert response.status_code == 400

    def test_me_patch_email_allows_keeping_own_address(self, api_client):
        _register(api_client, email="unchanged@example.com")
        login = _login(api_client, "unchanged@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = api_client.patch(
            "/api/v1/auth/me/", {"email": "unchanged@example.com"}, format="json"
        )

        assert response.status_code == 200


class TestTokenLifecycle:
    def test_refresh_rotates_and_blacklists_old_token(self, api_client):
        _register(api_client, email="rotate@example.com")
        old_refresh = _login(api_client, "rotate@example.com").data["refresh"]

        first_refresh = api_client.post(
            "/api/v1/auth/token/refresh/", {"refresh": old_refresh}, format="json"
        )
        assert first_refresh.status_code == 200
        assert "refresh" in first_refresh.data

        reuse_attempt = api_client.post(
            "/api/v1/auth/token/refresh/", {"refresh": old_refresh}, format="json"
        )
        assert reuse_attempt.status_code == 401

    def test_logout_blacklists_refresh_token(self, api_client):
        _register(api_client, email="logout@example.com")
        login = _login(api_client, "logout@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        logout_response = api_client.post(
            "/api/v1/auth/logout/", {"refresh": login.data["refresh"]}, format="json"
        )
        assert logout_response.status_code == 204
        assert AuditLog.objects.filter(action="user.logout").exists()

        reuse_attempt = api_client.post(
            "/api/v1/auth/token/refresh/", {"refresh": login.data["refresh"]}, format="json"
        )
        assert reuse_attempt.status_code == 401


class TestLoginRateLimiting:
    def test_login_is_rate_limited_past_configured_threshold(self, api_client, settings):
        # DRF's ScopedRateThrottle.THROTTLE_RATES is bound to
        # api_settings.DEFAULT_THROTTLE_RATES at import time, so overriding
        # settings.REST_FRAMEWORK mid-test has no effect on it — exercise the
        # real configured rate (settings.base.REST_FRAMEWORK) instead.
        limit = int(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["auth-login"].split("/")[0])

        for _ in range(limit):
            response = _login(api_client, "nobody@example.com", password="wrong")
            assert response.status_code == 401

        response = _login(api_client, "nobody@example.com", password="wrong")

        assert response.status_code == 429
