from datetime import timedelta

import pytest
from django.utils import timezone

from apps.catalog.models import Course
from apps.live_sessions.models import ConferencingAccount, LiveSession, LiveSessionRegistration
from apps.live_sessions.oauth_state import issue_state
from shared.crypto import encrypt

pytestmark = pytest.mark.django_db


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


@pytest.fixture
def instructor_client(api_client, instructor):
    api_client.force_authenticate(user=instructor)
    return api_client


@pytest.fixture
def student(django_user_model):
    return django_user_model.objects.create_user(email="student@example.com", password="x")


@pytest.fixture
def student_client(api_client, student):
    api_client.force_authenticate(user=student)
    return api_client


@pytest.fixture
def course(instructor):
    c = Course.objects.create(owner=instructor, title="Live Course")
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


@pytest.fixture
def conferencing_account(instructor):
    return ConferencingAccount.objects.create(
        user=instructor,
        provider=ConferencingAccount.PROVIDER_ZOOM,
        access_token_encrypted=encrypt("real-access-token"),
        refresh_token_encrypted=encrypt("real-refresh-token"),
        token_expires_at=timezone.now() + timedelta(hours=1),
    )


@pytest.fixture
def live_session(course, instructor, conferencing_account):
    now = timezone.now()
    return LiveSession.objects.create(
        course=course,
        host=instructor,
        conferencing_account=conferencing_account,
        provider=ConferencingAccount.PROVIDER_ZOOM,
        title="Kickoff Session",
        scheduled_start_at=now + timedelta(hours=1),
        scheduled_end_at=now + timedelta(hours=2),
        join_url="https://zoom.us/j/999",
        host_join_url="https://zoom.us/s/999",
        external_meeting_id="999",
    )


@pytest.fixture
def enrolled_student(student, course):
    from apps.learning.models import Enrollment

    Enrollment.objects.create(student=student, course=course)
    return student


@pytest.fixture
def registration(live_session, enrolled_student):
    return LiveSessionRegistration.objects.create(
        live_session=live_session, student=enrolled_student
    )


class TestConferencingAccountConnect:
    def test_connect_returns_authorization_url_with_signed_state(self, instructor_client, settings):
        settings.ZOOM_CLIENT_ID = "zoom-client"
        settings.ZOOM_REDIRECT_URI = "https://api.example.com/callback"

        response = instructor_client.post("/api/v1/instructor/conferencing-accounts/zoom/connect/")

        assert response.status_code == 200
        assert "authorization_url" in response.data
        assert "state=" in response.data["authorization_url"]

    def test_connect_unknown_provider_returns_404(self, instructor_client):
        response = instructor_client.post("/api/v1/instructor/conferencing-accounts/webex/connect/")

        assert response.status_code == 404

    def test_connect_requires_authentication(self, api_client):
        response = api_client.post("/api/v1/instructor/conferencing-accounts/zoom/connect/")

        assert response.status_code == 401


class TestConferencingAccountCallback:
    def test_callback_success_creates_account_and_redirects(
        self, api_client, instructor, monkeypatch, settings
    ):
        settings.PUBLIC_APP_URL = "https://app.example.com"
        state = issue_state(instructor.id, "zoom")
        monkeypatch.setattr(
            "apps.live_sessions.conferencing.zoom.requests.post",
            lambda *a, **k: type(
                "R",
                (),
                {
                    "status_code": 200,
                    "json": lambda self: {
                        "access_token": "real-at",
                        "refresh_token": "real-rt",
                        "expires_in": 3600,
                    },
                },
            )(),
        )

        response = api_client.get(
            "/api/v1/instructor/conferencing-accounts/zoom/callback/",
            {"code": "auth-code", "state": state},
        )

        assert response.status_code == 302
        assert response.url.startswith(
            "https://app.example.com/instructor/conferencing-accounts?connected=zoom"
        )
        account = ConferencingAccount.objects.get(user=instructor, provider="zoom")
        # The whole point of encrypting at rest: raw tokens never sit in
        # the database as plaintext.
        assert "real-at" not in account.access_token_encrypted
        assert "real-rt" not in account.refresh_token_encrypted

    def test_callback_invalid_state_redirects_with_error(self, api_client, settings):
        settings.PUBLIC_APP_URL = "https://app.example.com"

        response = api_client.get(
            "/api/v1/instructor/conferencing-accounts/zoom/callback/",
            {"code": "auth-code", "state": "garbage"},
        )

        assert response.status_code == 302
        assert "error=invalid_state" in response.url

    def test_callback_provider_state_mismatch_redirects_with_error(
        self, api_client, instructor, settings
    ):
        settings.PUBLIC_APP_URL = "https://app.example.com"
        state = issue_state(instructor.id, "google_meet")

        response = api_client.get(
            "/api/v1/instructor/conferencing-accounts/zoom/callback/",
            {"code": "auth-code", "state": state},
        )

        assert response.status_code == 302
        assert "error=invalid_state" in response.url


class TestConferencingAccountListAndRevoke:
    def test_list_never_exposes_encrypted_tokens(self, instructor_client, conferencing_account):
        response = instructor_client.get("/api/v1/instructor/conferencing-accounts/")

        assert response.status_code == 200
        body = str(response.data)
        assert "access_token_encrypted" not in body
        assert "refresh_token_encrypted" not in body

    def test_revoke_sets_revoked_at_and_hides_from_list(
        self, instructor_client, conferencing_account
    ):
        response = instructor_client.delete(
            f"/api/v1/instructor/conferencing-accounts/{conferencing_account.id}/"
        )
        assert response.status_code == 204

        listing = instructor_client.get("/api/v1/instructor/conferencing-accounts/")
        assert listing.data == []


class TestLiveSessionSchedule:
    def test_schedule_creates_session_via_provider(
        self, instructor_client, course, conferencing_account, monkeypatch
    ):
        monkeypatch.setattr(
            "apps.live_sessions.conferencing.zoom.requests.post",
            lambda *a, **k: type(
                "R",
                (),
                {
                    "status_code": 201,
                    "json": lambda self: {
                        "id": 42,
                        "join_url": "https://zoom.us/j/42",
                        "start_url": "https://zoom.us/s/42",
                    },
                },
            )(),
        )
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=1)

        response = instructor_client.post(
            f"/api/v1/instructor/courses/{course.id}/live-sessions/",
            {
                "conferencing_account_id": str(conferencing_account.id),
                "provider": "zoom",
                "title": "Deep Dive",
                "scheduled_start_at": start.isoformat(),
                "scheduled_end_at": end.isoformat(),
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["title"] == "Deep Dive"
        session = LiveSession.objects.get(id=response.data["id"])
        assert session.join_url == "https://zoom.us/j/42"
        assert session.external_meeting_id == "42"

    def test_schedule_rejects_end_before_start(
        self, instructor_client, course, conferencing_account
    ):
        start = timezone.now() + timedelta(days=1)

        response = instructor_client.post(
            f"/api/v1/instructor/courses/{course.id}/live-sessions/",
            {
                "conferencing_account_id": str(conferencing_account.id),
                "provider": "zoom",
                "title": "Bad Times",
                "scheduled_start_at": start.isoformat(),
                "scheduled_end_at": (start - timedelta(hours=1)).isoformat(),
            },
            format="json",
        )

        assert response.status_code == 400

    def test_schedule_rejects_non_owner(self, student_client, course, conferencing_account):
        start = timezone.now() + timedelta(days=1)

        response = student_client.post(
            f"/api/v1/instructor/courses/{course.id}/live-sessions/",
            {
                "conferencing_account_id": str(conferencing_account.id),
                "provider": "zoom",
                "title": "Not Mine",
                "scheduled_start_at": start.isoformat(),
                "scheduled_end_at": (start + timedelta(hours=1)).isoformat(),
            },
            format="json",
        )

        assert response.status_code == 403


class TestLiveSessionCancel:
    def test_cancel_marks_canceled_even_if_provider_call_fails(
        self, instructor_client, live_session, monkeypatch
    ):
        import requests

        def _boom(*a, **k):
            raise requests.exceptions.ConnectionError("network down")

        monkeypatch.setattr("apps.live_sessions.conferencing.zoom.requests.delete", _boom)

        response = instructor_client.post(
            f"/api/v1/instructor/live-sessions/{live_session.id}/cancel/"
        )

        assert response.status_code == 200
        live_session.refresh_from_db()
        assert live_session.status == LiveSession.STATUS_CANCELED

    def test_cancel_rejects_non_host(self, student_client, live_session):
        response = student_client.post(
            f"/api/v1/instructor/live-sessions/{live_session.id}/cancel/"
        )

        assert response.status_code == 403


class TestLiveSessionRegister:
    def test_register_requires_enrollment(self, student_client, live_session):
        response = student_client.post(f"/api/v1/live-sessions/{live_session.id}/register/")

        assert response.status_code == 403

    def test_register_succeeds_when_enrolled(self, student_client, enrolled_student, live_session):
        response = student_client.post(f"/api/v1/live-sessions/{live_session.id}/register/")

        assert response.status_code == 201
        assert LiveSessionRegistration.objects.filter(
            live_session=live_session, student=enrolled_student
        ).exists()

    def test_register_at_capacity_rejected(
        self, student_client, enrolled_student, live_session, django_user_model
    ):
        live_session.capacity = 1
        live_session.save(update_fields=["capacity"])
        other = django_user_model.objects.create_user(email="other@example.com", password="x")
        from apps.learning.models import Enrollment

        Enrollment.objects.create(student=other, course=live_session.course)
        LiveSessionRegistration.objects.create(live_session=live_session, student=other)

        response = student_client.post(f"/api/v1/live-sessions/{live_session.id}/register/")

        assert response.status_code == 400

    def test_unregister(self, student_client, registration, live_session):
        response = student_client.delete(f"/api/v1/live-sessions/{live_session.id}/register/")

        assert response.status_code == 204
        registration.refresh_from_db()
        assert registration.status == LiveSessionRegistration.STATUS_CANCELED


class TestLiveSessionJoinWindowGating:
    """
    The security-critical path: join links must never be handed out
    outside the registered window, regardless of who's asking.
    """

    def test_join_rejected_when_not_registered(self, student_client, live_session):
        response = student_client.get(f"/api/v1/live-sessions/{live_session.id}/join/")

        assert response.status_code == 403

    def test_join_rejected_too_early(self, student_client, registration, live_session):
        # scheduled_start_at is 1 hour from now; window opens 15 min before.
        response = student_client.get(f"/api/v1/live-sessions/{live_session.id}/join/")

        assert response.status_code == 403

    def test_join_allowed_at_window_open(self, student_client, registration, live_session):
        live_session.scheduled_start_at = timezone.now() + timedelta(minutes=10)
        live_session.scheduled_end_at = timezone.now() + timedelta(hours=1)
        live_session.save(update_fields=["scheduled_start_at", "scheduled_end_at"])

        response = student_client.get(f"/api/v1/live-sessions/{live_session.id}/join/")

        assert response.status_code == 200
        assert response.data["join_url"] == live_session.join_url
        registration.refresh_from_db()
        assert registration.status == LiveSessionRegistration.STATUS_ATTENDED
        assert registration.joined_at is not None

    def test_join_rejected_after_session_end(self, student_client, registration, live_session):
        live_session.scheduled_start_at = timezone.now() - timedelta(hours=2)
        live_session.scheduled_end_at = timezone.now() - timedelta(hours=1)
        live_session.save(update_fields=["scheduled_start_at", "scheduled_end_at"])

        response = student_client.get(f"/api/v1/live-sessions/{live_session.id}/join/")

        assert response.status_code == 403

    def test_join_rejected_for_canceled_registration(
        self, student_client, registration, live_session
    ):
        registration.status = LiveSessionRegistration.STATUS_CANCELED
        registration.save(update_fields=["status"])
        live_session.scheduled_start_at = timezone.now() + timedelta(minutes=10)
        live_session.save(update_fields=["scheduled_start_at"])

        response = student_client.get(f"/api/v1/live-sessions/{live_session.id}/join/")

        assert response.status_code == 403

    def test_join_rejected_for_canceled_session(self, student_client, registration, live_session):
        live_session.scheduled_start_at = timezone.now() + timedelta(minutes=10)
        live_session.status = LiveSession.STATUS_CANCELED
        live_session.save(update_fields=["scheduled_start_at", "status"])

        response = student_client.get(f"/api/v1/live-sessions/{live_session.id}/join/")

        assert response.status_code == 403


class TestLiveSessionRecording:
    def test_recording_not_found_before_available(self, student_client, registration, live_session):
        response = student_client.get(f"/api/v1/live-sessions/{live_session.id}/recording/")

        assert response.status_code == 404

    def test_recording_visible_to_registered_student(
        self, student_client, registration, live_session
    ):
        from apps.live_sessions.models import LiveSessionRecording

        LiveSessionRecording.objects.create(
            live_session=live_session,
            playback_url="https://zoom.us/rec/123",
            duration_seconds=1800,
            available_at=timezone.now(),
        )

        response = student_client.get(f"/api/v1/live-sessions/{live_session.id}/recording/")

        assert response.status_code == 200
        assert response.data["playback_url"] == "https://zoom.us/rec/123"

    def test_recording_hidden_from_non_registered_user(
        self, api_client, django_user_model, live_session
    ):
        from apps.live_sessions.models import LiveSessionRecording

        LiveSessionRecording.objects.create(
            live_session=live_session,
            playback_url="https://zoom.us/rec/123",
            duration_seconds=1800,
            available_at=timezone.now(),
        )
        stranger = django_user_model.objects.create_user(email="stranger@example.com", password="x")
        api_client.force_authenticate(user=stranger)

        response = api_client.get(f"/api/v1/live-sessions/{live_session.id}/recording/")

        assert response.status_code == 403


class TestLiveSessionRegistrationsListing:
    def test_host_sees_registrations(self, instructor_client, live_session, registration):
        response = instructor_client.get(
            f"/api/v1/instructor/live-sessions/{live_session.id}/registrations/"
        )

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_non_host_forbidden(self, student_client, live_session, registration):
        response = student_client.get(
            f"/api/v1/instructor/live-sessions/{live_session.id}/registrations/"
        )

        assert response.status_code == 403
