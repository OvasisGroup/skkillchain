import pyotp
import pytest

from apps.audit.models import AuditLog
from apps.identity.models import MFAFactor

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "a-strong-password-1"


def _register_and_login(api_client, email):
    api_client.post(
        "/api/v1/auth/register/", {"email": email, "password": STRONG_PASSWORD}, format="json"
    )
    login = api_client.post(
        "/api/v1/auth/login/", {"email": email, "password": STRONG_PASSWORD}, format="json"
    )
    return login.data["access"]


class TestMFAEnrollAndVerify:
    def test_enroll_then_verify_confirms_factor(self, api_client):
        access = _register_and_login(api_client, "mfa@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        enroll = api_client.post("/api/v1/auth/mfa/enroll/")
        assert enroll.status_code == 201
        assert "otpauth://" in enroll.data["provisioning_uri"]
        secret = enroll.data["secret"]

        verify = api_client.post(
            "/api/v1/auth/mfa/verify/", {"code": pyotp.TOTP(secret).now()}, format="json"
        )

        assert verify.status_code == 200
        factor = MFAFactor.objects.get(user__email="mfa@example.com")
        assert factor.confirmed_at is not None
        assert AuditLog.objects.filter(action="mfa.enroll_confirmed").exists()

    def test_verify_rejects_wrong_code(self, api_client):
        access = _register_and_login(api_client, "mfa2@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        api_client.post("/api/v1/auth/mfa/enroll/")

        response = api_client.post("/api/v1/auth/mfa/verify/", {"code": "000000"}, format="json")

        assert response.status_code == 401
        assert AuditLog.objects.filter(action="mfa.verify_failed").exists()

    def test_verify_without_pending_enrollment_returns_404(self, api_client):
        access = _register_and_login(api_client, "mfa3@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = api_client.post("/api/v1/auth/mfa/verify/", {"code": "123456"}, format="json")

        assert response.status_code == 404

    def test_reenrolling_discards_previous_pending_factor(self, api_client):
        access = _register_and_login(api_client, "mfa4@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        api_client.post("/api/v1/auth/mfa/enroll/")

        api_client.post("/api/v1/auth/mfa/enroll/")

        assert MFAFactor.objects.filter(user__email="mfa4@example.com").count() == 1


class TestMFALoginFlow:
    def _enroll_and_confirm(self, api_client, email):
        access = _register_and_login(api_client, email)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        enroll = api_client.post("/api/v1/auth/mfa/enroll/")
        secret = enroll.data["secret"]
        api_client.post(
            "/api/v1/auth/mfa/verify/", {"code": pyotp.TOTP(secret).now()}, format="json"
        )
        api_client.credentials()  # clear auth before the next fresh login attempt
        return secret

    def test_login_with_confirmed_mfa_withholds_tokens(self, api_client):
        self._enroll_and_confirm(api_client, "mfalogin@example.com")

        login = api_client.post(
            "/api/v1/auth/login/",
            {"email": "mfalogin@example.com", "password": STRONG_PASSWORD},
            format="json",
        )

        assert login.status_code == 202
        assert login.data["mfa_required"] is True
        assert "access" not in login.data
        assert "refresh" not in login.data

    def test_login_verify_completes_login_with_correct_code(self, api_client):
        secret = self._enroll_and_confirm(api_client, "mfalogin2@example.com")
        login = api_client.post(
            "/api/v1/auth/login/",
            {"email": "mfalogin2@example.com", "password": STRONG_PASSWORD},
            format="json",
        )

        response = api_client.post(
            "/api/v1/auth/mfa/login-verify/",
            {"mfa_token": login.data["mfa_token"], "code": pyotp.TOTP(secret).now()},
            format="json",
        )

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        assert AuditLog.objects.filter(action="user.login", payload__mfa=True).exists()

    def test_login_verify_rejects_wrong_code(self, api_client):
        self._enroll_and_confirm(api_client, "mfalogin3@example.com")
        login = api_client.post(
            "/api/v1/auth/login/",
            {"email": "mfalogin3@example.com", "password": STRONG_PASSWORD},
            format="json",
        )

        response = api_client.post(
            "/api/v1/auth/mfa/login-verify/",
            {"mfa_token": login.data["mfa_token"], "code": "000000"},
            format="json",
        )

        assert response.status_code == 401

    def test_login_verify_rejects_garbage_token(self, api_client):
        response = api_client.post(
            "/api/v1/auth/mfa/login-verify/",
            {"mfa_token": "garbage", "code": "123456"},
            format="json",
        )

        assert response.status_code == 401

    def test_login_without_mfa_still_returns_tokens_directly(self, api_client):
        api_client.post(
            "/api/v1/auth/register/",
            {"email": "nomfa@example.com", "password": STRONG_PASSWORD},
            format="json",
        )

        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": "nomfa@example.com", "password": STRONG_PASSWORD},
            format="json",
        )

        assert response.status_code == 200
        assert "access" in response.data
