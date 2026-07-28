from datetime import datetime, timezone

import pytest

from apps.live_sessions.conferencing.base import ConferencingProviderError
from apps.live_sessions.conferencing.google_meet import GoogleMeetConferencingProvider
from apps.live_sessions.conferencing.registry import get_provider
from apps.live_sessions.conferencing.zoom import ZoomConferencingProvider


class _FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text or str(payload)

    def json(self):
        return self._payload


class TestZoomConferencingProvider:
    def test_authorization_url_contains_client_id_and_state(self, settings):
        settings.ZOOM_CLIENT_ID = "zoom-client"
        settings.ZOOM_REDIRECT_URI = "https://api.example.com/callback"

        url = ZoomConferencingProvider().authorization_url("opaque-state")

        assert "client_id=zoom-client" in url
        assert "state=opaque-state" in url

    def test_exchange_code_for_tokens_success(self, monkeypatch):
        monkeypatch.setattr(
            "apps.live_sessions.conferencing.zoom.requests.post",
            lambda *a, **k: _FakeResponse(
                200, {"access_token": "at", "refresh_token": "rt", "expires_in": 3600}
            ),
        )

        tokens = ZoomConferencingProvider().exchange_code_for_tokens("code")

        assert tokens.access_token == "at"
        assert tokens.refresh_token == "rt"

    def test_exchange_code_for_tokens_failure_raises(self, monkeypatch):
        monkeypatch.setattr(
            "apps.live_sessions.conferencing.zoom.requests.post",
            lambda *a, **k: _FakeResponse(400, {"error": "invalid_grant"}),
        )

        with pytest.raises(ConferencingProviderError):
            ZoomConferencingProvider().exchange_code_for_tokens("bad-code")

    def test_create_meeting_success(self, monkeypatch):
        monkeypatch.setattr(
            "apps.live_sessions.conferencing.zoom.requests.post",
            lambda *a, **k: _FakeResponse(
                201,
                {
                    "id": 123456789,
                    "join_url": "https://zoom.us/j/123",
                    "start_url": "https://zoom.us/s/123",
                },
            ),
        )

        meeting = ZoomConferencingProvider().create_meeting(
            "at",
            title="Live Q&A",
            description="",
            start_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc),
        )

        assert meeting.external_meeting_id == "123456789"
        assert meeting.join_url == "https://zoom.us/j/123"
        assert meeting.host_join_url == "https://zoom.us/s/123"

    def test_get_recording_returns_none_on_404(self, monkeypatch):
        monkeypatch.setattr(
            "apps.live_sessions.conferencing.zoom.requests.get", lambda *a, **k: _FakeResponse(404)
        )

        assert ZoomConferencingProvider().get_recording("at", "123") is None

    def test_cancel_meeting_raises_on_unexpected_status(self, monkeypatch):
        monkeypatch.setattr(
            "apps.live_sessions.conferencing.zoom.requests.delete",
            lambda *a, **k: _FakeResponse(500, text="boom"),
        )

        with pytest.raises(ConferencingProviderError):
            ZoomConferencingProvider().cancel_meeting("at", "123")


class TestGoogleMeetConferencingProvider:
    def test_create_meeting_extracts_video_entry_point(self, monkeypatch):
        monkeypatch.setattr(
            "apps.live_sessions.conferencing.google_meet.requests.post",
            lambda *a, **k: _FakeResponse(
                200,
                {
                    "id": "evt-1",
                    "conferenceData": {
                        "entryPoints": [
                            {
                                "entryPointType": "video",
                                "uri": "https://meet.google.com/abc-defg-hij",
                            }
                        ]
                    },
                },
            ),
        )

        meeting = GoogleMeetConferencingProvider().create_meeting(
            "at",
            title="Office Hours",
            description="",
            start_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc),
        )

        assert meeting.external_meeting_id == "evt-1"
        assert meeting.join_url == "https://meet.google.com/abc-defg-hij"
        # No separate host URL for Google Meet — same link for both.
        assert meeting.host_join_url == meeting.join_url

    def test_get_recording_returns_none_when_no_files(self, monkeypatch):
        monkeypatch.setattr(
            "apps.live_sessions.conferencing.google_meet.requests.get",
            lambda *a, **k: _FakeResponse(200, {"files": []}),
        )

        assert GoogleMeetConferencingProvider().get_recording("at", "evt-1") is None

    def test_get_recording_picks_newest_file(self, monkeypatch):
        monkeypatch.setattr(
            "apps.live_sessions.conferencing.google_meet.requests.get",
            lambda *a, **k: _FakeResponse(
                200,
                {
                    "files": [
                        {
                            "id": "file-1",
                            "webViewLink": "https://drive.google.com/file/file-1",
                            "videoMediaMetadata": {"durationMillis": "60000"},
                        }
                    ]
                },
            ),
        )

        recording = GoogleMeetConferencingProvider().get_recording("at", "evt-1")

        assert recording.provider_recording_id == "file-1"
        assert recording.duration_seconds == 60


class TestRegistry:
    def test_get_provider_returns_adapter_for_known_code(self):
        assert isinstance(get_provider("zoom"), ZoomConferencingProvider)
        assert isinstance(get_provider("google_meet"), GoogleMeetConferencingProvider)

    def test_get_provider_returns_none_for_unknown_code(self):
        assert get_provider("webex") is None
