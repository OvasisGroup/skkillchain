import datetime
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from . import aggregation

logger = logging.getLogger(__name__)


@shared_task(name="analytics.aggregate_daily", time_limit=300)
def aggregate_daily(target_date: str | None = None) -> dict:
    """Computes yesterday's (or an explicitly passed ISO date's) rollups
    across all six report tables. Idempotent — every aggregator upserts
    keyed on its period, so re-running for the same date recomputes
    rather than duplicates."""
    if target_date:
        period_start = datetime.date.fromisoformat(target_date)
    else:
        period_start = (timezone.now() - timedelta(days=1)).date()
    period_end = period_start + timedelta(days=1)

    counts = {
        "revenue": aggregation.aggregate_revenue(period_start, period_end),
        "engagement": aggregation.aggregate_engagement(period_start, period_end),
        "completion": aggregation.aggregate_completion(period_start, period_end),
        "watch_time": aggregation.aggregate_watch_time(period_start, period_end),
        "drop_off": aggregation.aggregate_drop_off(period_start, period_end),
        "instructor_earnings": aggregation.aggregate_instructor_earnings(period_start, period_end),
    }
    logger.info("analytics.aggregate_daily: %s for %s", counts, period_start)
    return counts
