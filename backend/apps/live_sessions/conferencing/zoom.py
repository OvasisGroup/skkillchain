from urllib.parse import urlencode

import requests
from django.conf import settings

from .base import (
    ConferencingProvider,
    ConferencingProviderError,
    MeetingInfo,
    OAuthTokens,
    RecordingInfo,
)

_AUTHORIZE_URL = "https://zoom.us/oauth/authorize"
_TOKEN_URL = "https://zoom.us/oauth/token"
_API_BASE = "https://api.zoom.us/v2"


def _call(method, *args, **kwargs):
    # Wraps every outbound call so a raw network failure (timeout, DNS,
    # connection refused) surfaces as ConferencingProviderError just like a
    # bad HTTP status does — callers only ever need to catch one exception
    # type, not `requests`' whole hierarchy too.
    try:
        return method(*args, **kwargs)
    except requests.exceptions.RequestException as exc:
        raise ConferencingProviderError(f"Zoom request failed: {exc}") from exc


class ZoomConferencingProvider(ConferencingProvider):
    code = "zoom"

    def authorization_url(self, state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": settings.ZOOM_CLIENT_ID,
            "redirect_uri": settings.ZOOM_REDIRECT_URI,
            "state": state,
        }
        return f"{_AUTHORIZE_URL}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str) -> OAuthTokens:
        response = _call(
            requests.post,
            _TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.ZOOM_REDIRECT_URI,
            },
            auth=(settings.ZOOM_CLIENT_ID, settings.ZOOM_CLIENT_SECRET),
            timeout=10,
        )
        if response.status_code != 200:
            raise ConferencingProviderError(f"Zoom token exchange failed: {response.text}")
        data = response.json()
        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            expires_in=data.get("expires_in", 3600),
        )

    def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        response = _call(
            requests.post,
            _TOKEN_URL,
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            auth=(settings.ZOOM_CLIENT_ID, settings.ZOOM_CLIENT_SECRET),
            timeout=10,
        )
        if response.status_code != 200:
            raise ConferencingProviderError(f"Zoom token refresh failed: {response.text}")
        data = response.json()
        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            expires_in=data.get("expires_in", 3600),
        )

    def create_meeting(self, access_token, *, title, description, start_at, end_at):
        duration_minutes = max(1, int((end_at - start_at).total_seconds() // 60))
        response = _call(
            requests.post,
            f"{_API_BASE}/users/me/meetings",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "topic": title,
                "agenda": description,
                "type": 2,  # scheduled meeting
                "start_time": start_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "duration": duration_minutes,
                "timezone": "UTC",
                "settings": {"join_before_host": False, "waiting_room": True},
            },
            timeout=10,
        )
        if response.status_code not in (200, 201):
            raise ConferencingProviderError(f"Zoom meeting creation failed: {response.text}")
        data = response.json()
        return MeetingInfo(
            external_meeting_id=str(data["id"]),
            join_url=data["join_url"],
            host_join_url=data.get("start_url", data["join_url"]),
        )

    def cancel_meeting(self, access_token, external_meeting_id):
        response = _call(
            requests.delete,
            f"{_API_BASE}/meetings/{external_meeting_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if response.status_code not in (204, 404):
            raise ConferencingProviderError(f"Zoom meeting cancellation failed: {response.text}")

    def get_recording(self, access_token, external_meeting_id):
        response = _call(
            requests.get,
            f"{_API_BASE}/meetings/{external_meeting_id}/recordings",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise ConferencingProviderError(f"Zoom recording lookup failed: {response.text}")

        data = response.json()
        files = data.get("recording_files", [])
        if not files:
            return None
        video_file = next((f for f in files if f.get("file_type") == "MP4"), files[0])
        return RecordingInfo(
            provider_recording_id=str(data.get("uuid", external_meeting_id)),
            playback_url=video_file.get("play_url", ""),
            duration_seconds=int(data.get("duration", 0)) * 60,
        )
