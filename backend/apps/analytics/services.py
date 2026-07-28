from .models import AnalyticsEvent


def record_analytics_event(
    event_name: str, *, actor=None, course=None, session_id: str = "", payload: dict | None = None
) -> AnalyticsEvent:
    return AnalyticsEvent.objects.create(
        event_name=event_name,
        actor=actor,
        course=course,
        session_id=session_id,
        payload=payload or {},
    )
