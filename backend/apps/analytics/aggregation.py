import datetime
from decimal import Decimal

from django.db.models import Count, Sum

from apps.catalog.models import Course
from apps.commerce.models import Payment, Refund
from apps.content.models import Lesson
from apps.learning.models import Enrollment, ProgressTracking
from apps.payouts.models import Transaction, Wallet

from .models import (
    CourseCompletionAggregate,
    EngagementDailyAggregate,
    InstructorEarningsAggregate,
    LessonDropOffAggregate,
    LessonWatchTimeAggregate,
    RevenueDailyAggregate,
)


def aggregate_revenue(period_start: datetime.date, period_end: datetime.date) -> int:
    rows = (
        Payment.objects.filter(
            status=Payment.STATUS_SUCCEEDED,
            paid_at__date__gte=period_start,
            paid_at__date__lt=period_end,
        )
        .values("currency")
        .annotate(gross=Sum("amount"))
    )
    count = 0
    for row in rows:
        currency = row["currency"]
        gross = row["gross"] or Decimal("0")
        refunded = (
            Refund.objects.filter(
                status=Refund.STATUS_SUCCEEDED,
                payment__currency=currency,
                requested_at__date__gte=period_start,
                requested_at__date__lt=period_end,
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )
        RevenueDailyAggregate.objects.update_or_create(
            period_start=period_start,
            period_end=period_end,
            currency=currency,
            defaults={"gross_amount": gross, "net_amount": gross - refunded},
        )
        count += 1
    return count


def aggregate_engagement(period_start: datetime.date, period_end: datetime.date) -> int:
    new_enrollment_course_ids = Enrollment.objects.filter(
        enrolled_at__date__gte=period_start, enrolled_at__date__lt=period_end
    ).values_list("course_id", flat=True)
    active_course_ids = ProgressTracking.objects.filter(
        last_viewed_at__date__gte=period_start, last_viewed_at__date__lt=period_end
    ).values_list("enrollment__course_id", flat=True)
    course_ids = set(new_enrollment_course_ids) | set(active_course_ids)

    count = 0
    for course_id in course_ids:
        new_enrollments = Enrollment.objects.filter(
            course_id=course_id, enrolled_at__date__gte=period_start, enrolled_at__date__lt=period_end
        ).count()
        active_students = (
            ProgressTracking.objects.filter(
                enrollment__course_id=course_id,
                last_viewed_at__date__gte=period_start,
                last_viewed_at__date__lt=period_end,
            )
            .values("enrollment__student_id")
            .distinct()
            .count()
        )
        EngagementDailyAggregate.objects.update_or_create(
            course_id=course_id,
            period_start=period_start,
            period_end=period_end,
            defaults={"active_students_count": active_students, "new_enrollments_count": new_enrollments},
        )
        count += 1
    return count


def aggregate_completion(period_start: datetime.date, period_end: datetime.date) -> int:
    # Cumulative as-of period_end, not a single day's delta — a completion
    # *rate* is a running state, so each day's row is a snapshot of
    # all-time enrollments/completions up to that date.
    course_ids = Course.objects.filter(enrollments__isnull=False).values_list("id", flat=True).distinct()
    count = 0
    for course_id in course_ids:
        enrollments_count = Enrollment.objects.filter(
            course_id=course_id, enrolled_at__date__lt=period_end
        ).count()
        completions_count = Enrollment.objects.filter(
            course_id=course_id,
            status=Enrollment.STATUS_COMPLETED,
            completed_at__date__lt=period_end,
        ).count()
        rate = (
            Decimal(completions_count) / Decimal(enrollments_count) * 100
            if enrollments_count
            else Decimal("0")
        )
        CourseCompletionAggregate.objects.update_or_create(
            course_id=course_id,
            period_start=period_start,
            period_end=period_end,
            defaults={
                "enrollments_count": enrollments_count,
                "completions_count": completions_count,
                "completion_rate": rate,
            },
        )
        count += 1
    return count


def aggregate_watch_time(period_start: datetime.date, period_end: datetime.date) -> int:
    rows = (
        ProgressTracking.objects.filter(
            last_viewed_at__date__gte=period_start, last_viewed_at__date__lt=period_end
        )
        .values("lesson_id")
        .annotate(total_seconds=Sum("last_position_seconds"), views=Count("id"))
    )
    count = 0
    for row in rows:
        LessonWatchTimeAggregate.objects.update_or_create(
            lesson_id=row["lesson_id"],
            period_start=period_start,
            period_end=period_end,
            defaults={"total_watch_seconds": row["total_seconds"] or 0, "views_count": row["views"]},
        )
        count += 1
    return count


def aggregate_drop_off(period_start: datetime.date, period_end: datetime.date) -> int:
    # Cumulative snapshot, not a true per-day figure: ProgressTracking has
    # no created_at/started_at field — only last_viewed_at, overwritten on
    # every view — so "started as of this date" can't be reconstructed
    # historically. started_count/completed_count reflect current totals
    # regardless of which period is passed in; only computed_at (auto_now)
    # actually varies run to run.
    lesson_ids = (
        Lesson.objects.filter(progress_entries__isnull=False).values_list("id", flat=True).distinct()
    )
    count = 0
    for lesson_id in lesson_ids:
        started = ProgressTracking.objects.filter(lesson_id=lesson_id).count()
        completed = ProgressTracking.objects.filter(lesson_id=lesson_id, percent_complete__gte=100).count()
        rate = Decimal(started - completed) / Decimal(started) * 100 if started else Decimal("0")
        LessonDropOffAggregate.objects.update_or_create(
            lesson_id=lesson_id,
            period_start=period_start,
            period_end=period_end,
            defaults={"started_count": started, "completed_count": completed, "drop_off_rate": rate},
        )
        count += 1
    return count


def aggregate_instructor_earnings(period_start: datetime.date, period_end: datetime.date) -> int:
    rows = (
        Transaction.objects.filter(
            wallet__owner_type=Wallet.OWNER_INSTRUCTOR,
            direction=Transaction.DIRECTION_CREDIT,
            created_at__date__gte=period_start,
            created_at__date__lt=period_end,
        )
        .values("wallet__owner_id", "wallet__currency")
        .annotate(total=Sum("amount"))
    )
    count = 0
    for row in rows:
        # The ledger only records the instructor's net share — platform
        # commission was already subtracted before crediting (see
        # apps.commerce.services.finalize_order_payment) — so there's no
        # gross pre-commission figure preserved at the transaction level.
        # gross mirrors net here rather than reconstructing a synthetic
        # gross via PLATFORM_COMMISSION_RATE.
        InstructorEarningsAggregate.objects.update_or_create(
            instructor_id=row["wallet__owner_id"],
            period_start=period_start,
            period_end=period_end,
            currency=row["wallet__currency"],
            defaults={"gross_amount": row["total"], "net_amount": row["total"]},
        )
        count += 1
    return count
