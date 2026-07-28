import uuid
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

_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_CALENDAR_API = "https://www.googleapis.com/calendar/v3"
_DRIVE_API = "https://www.googleapis.com/drive/v3"
_SCOPES = (
    "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/drive.readonly"
)


def _call(method, *args, **kwargs):
    # Same reasoning as conferencing/zoom.py's _call: convert raw network
    # failures into ConferencingProviderError so callers have one exception
    # type to handle instead of requests' whole hierarchy too.
    try:
        return method(*args, **kwargs)
    except requests.exceptions.RequestException as exc:
        raise ConferencingProviderError(f"Google Meet request failed: {exc}") from exc


class GoogleMeetConferencingProvider(ConferencingProvider):
    code = "google_meet"

    def authorization_url(self, state: str) -> str:
        params = {
            "client_id": settings.GOOGLE_MEET_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_MEET_REDIRECT_URI,
            "response_type": "code",
            "scope": _SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{_AUTHORIZE_URL}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str) -> OAuthTokens:
        response = _call(
            requests.post,
            _TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_MEET_CLIENT_ID,
                "client_secret": settings.GOOGLE_MEET_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_MEET_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        if response.status_code != 200:
            raise ConferencingProviderError(f"Google token exchange failed: {response.text}")
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
            data={
                "refresh_token": refresh_token,
                "client_id": settings.GOOGLE_MEET_CLIENT_ID,
                "client_secret": settings.GOOGLE_MEET_CLIENT_SECRET,
                "grant_type": "refresh_token",
            },
            timeout=10,
        )
        if response.status_code != 200:
            raise ConferencingProviderError(f"Google token refresh failed: {response.text}")
        data = response.json()
        return OAuthTokens(
            access_token=data["access_token"],
            # Google often omits refresh_token on refresh responses — keep
            # the one we already had.
            refresh_token=data.get("refresh_token", refresh_token),
            expires_in=data.get("expires_in", 3600),
        )

    def create_meeting(self, access_token, *, title, description, start_at, end_at):
        response = _call(
            requests.post,
            f"{_CALENDAR_API}/calendars/primary/events",
            params={"conferenceDataVersion": 1},
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "summary": title,
                "description": description,
                "start": {"dateTime": start_at.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end_at.isoformat(), "timeZone": "UTC"},
                "conferenceData": {
                    "createRequest": {
                        "requestId": str(uuid.uuid4()),
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                },
            },
            timeout=10,
        )
        if response.status_code not in (200, 201):
            raise ConferencingProviderError(f"Google Meet creation failed: {response.text}")

        data = response.json()
        entry_points = data.get("conferenceData", {}).get("entryPoints", [])
        video_entry = next((e for e in entry_points if e.get("entryPointType") == "video"), None)
        join_url = video_entry["uri"] if video_entry else ""
        return MeetingInfo(
            external_meeting_id=data["id"],
            join_url=join_url,
            # Google Meet has no separate host-start URL the way Zoom
            # does — the host joins the same link, authenticated as owner.
            host_join_url=join_url,
        )

    def cancel_meeting(self, access_token, external_meeting_id):
        response = _call(
            requests.delete,
            f"{_CALENDAR_API}/calendars/primary/events/{external_meeting_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if response.status_code not in (204, 410, 404):
            raise ConferencingProviderError(f"Google Meet cancellation failed: {response.text}")

    def get_recording(self, access_token, external_meeting_id):
        # Best-effort only: unlike Zoom's recording.completed webhook,
        # Google Meet recordings land in the host's Drive with no direct
        # "recording for this event" API — see
        # docs/01-architecture/01-technical-architecture.md §3.1. This
        # searches Drive for the most recently modified video file, which
        # is a reasonable heuristic for a single active recording but not
        # a guarantee against a false match if the host records other
        # videos around the same time.
        response = _call(
            requests.get,
            f"{_DRIVE_API}/files",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "q": "mimeType contains 'video/' and trashed = false",
                "orderBy": "modifiedTime desc",
                "pageSize": 5,
                "fields": "files(id,name,webViewLink,videoMediaMetadata)",
            },
            timeout=10,
        )
        if response.status_code != 200:
            raise ConferencingProviderError(f"Google Drive lookup failed: {response.text}")

        files = response.json().get("files", [])
        if not files:
            return None
        newest = files[0]
        duration_ms = newest.get("videoMediaMetadata", {}).get("durationMillis")
        return RecordingInfo(
            provider_recording_id=newest["id"],
            playback_url=newest.get("webViewLink", ""),
            duration_seconds=int(duration_ms) // 1000 if duration_ms else 0,
        )
