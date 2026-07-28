import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from shared.crypto import decrypt

from .conferencing.base import ConferencingProviderError
from .conferencing.registry import get_provider
from .models import LiveSession, LiveSessionRecording, LiveSessionRegistration

logger = logging.getLogger(__name__)


@shared_task(name="live_sessions.dispatch_reminders", time_limit=60)
def dispatch_reminders() -> int:
    """
    Finds registrations for sessions starting in the next hour that haven't
    been reminded yet. There is no notification channel wired up yet
    (email/push is M7), so this only identifies who *would* be reminded —
    it logs the count rather than pretending to send anything. Wiring this
    into a real send is a follow-up, not a bug in this task.
    """
    window_end = timezone.now() + timedelta(hours=1)
    due = LiveSessionRegistration.objects.filter(
        status=LiveSessionRegistration.STATUS_REGISTERED,
        live_session__scheduled_start_at__gt=timezone.now(),
        live_session__scheduled_start_at__lte=window_end,
        live_session__status=LiveSession.STATUS_SCHEDULED,
    ).select_related("live_session", "student")

    count = due.count()
    logger.info(
        "live_sessions.dispatch_reminders: %d registrations due for a reminder (no send channel yet)",
        count,
    )
    return count


@shared_task(name="live_sessions.poll_google_meet_recordings", time_limit=120)
def poll_google_meet_recordings() -> int:
    """
    Google Meet has no recording-ready webhook (unlike Zoom), so recordings
    are found by polling — see the heuristic documented in
    conferencing/google_meet.py get_recording().
    """
    candidates = LiveSession.objects.filter(
        provider="google_meet",
        status=LiveSession.STATUS_ENDED,
        is_recorded=True,
        recording__isnull=True,
    ).select_related("conferencing_account")

    found = 0
    for live_session in candidates:
        account = live_session.conferencing_account
        if not account.is_active:
            continue
        provider_adapter = get_provider(live_session.provider)
        if provider_adapter is None:
            continue
        access_token = decrypt(account.access_token_encrypted)
        try:
            recording = provider_adapter.get_recording(
                access_token, live_session.external_meeting_id
            )
        except ConferencingProviderError:
            logger.exception(
                "live_sessions.poll_google_meet_recordings: lookup failed for %s", live_session.id
            )
            continue
        if recording is None:
            continue
        LiveSessionRecording.objects.create(
            live_session=live_session,
            provider_recording_id=recording.provider_recording_id,
            playback_url=recording.playback_url,
            duration_seconds=recording.duration_seconds,
            available_at=timezone.now(),
        )
        found += 1
    return found


@shared_task(name="live_sessions.close_ended_sessions", time_limit=60)
def close_ended_sessions() -> int:
    """Flips sessions past their scheduled_end_at to 'ended', and marks
    anyone who registered but never joined as a no-show."""
    now = timezone.now()
    ended = LiveSession.objects.filter(
        status__in=[LiveSession.STATUS_SCHEDULED, LiveSession.STATUS_LIVE], scheduled_end_at__lt=now
    )
    count = ended.count()
    ids = list(ended.values_list("id", flat=True))
    ended.update(status=LiveSession.STATUS_ENDED)

    LiveSessionRegistration.objects.filter(
        live_session_id__in=ids, status=LiveSessionRegistration.STATUS_REGISTERED
    ).update(status=LiveSessionRegistration.STATUS_NO_SHOW)

    return count
