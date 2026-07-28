from dataclasses import dataclass
from datetime import datetime


@dataclass
class OAuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int  # seconds


@dataclass
class MeetingInfo:
    external_meeting_id: str
    join_url: str
    host_join_url: str


@dataclass
class RecordingInfo:
    provider_recording_id: str
    playback_url: str
    duration_seconds: int


class ConferencingProviderError(Exception):
    """Raised on any failure talking to the provider — the view maps this
    to a clear error rather than a bare 500."""


class ConferencingProvider:
    code: str = ""

    def authorization_url(self, state: str) -> str:
        raise NotImplementedError

    def exchange_code_for_tokens(self, code: str) -> OAuthTokens:
        raise NotImplementedError

    def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        raise NotImplementedError

    def create_meeting(
        self,
        access_token: str,
        *,
        title: str,
        description: str,
        start_at: datetime,
        end_at: datetime,
    ) -> MeetingInfo:
        raise NotImplementedError

    def cancel_meeting(self, access_token: str, external_meeting_id: str) -> None:
        raise NotImplementedError

    def get_recording(self, access_token: str, external_meeting_id: str) -> RecordingInfo | None:
        raise NotImplementedError
