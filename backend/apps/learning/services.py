import secrets

from django.conf import settings
from django.utils import timezone

from apps.content.models import Lesson

from .certificates import ensure_certificate_pdf
from .models import Certificate, Enrollment


def maybe_complete_enrollment(enrollment: Enrollment) -> Certificate | None:
    """Called after every progress update. Completion rule: every lesson in
    the course has a progress row at 100% — see
    docs/04-platform-structure/02-core-flows.md §5."""
    if enrollment.status == Enrollment.STATUS_COMPLETED:
        return None

    total_lessons = Lesson.objects.filter(section__course_id=enrollment.course_id).count()
    if total_lessons == 0:
        return None

    completed_lessons = enrollment.progress_entries.filter(percent_complete__gte=100).count()
    if completed_lessons < total_lessons:
        return None

    enrollment.status = Enrollment.STATUS_COMPLETED
    enrollment.completed_at = timezone.now()
    enrollment.save(update_fields=["status", "completed_at"])

    return issue_certificate(enrollment)


def issue_certificate(enrollment: Enrollment) -> Certificate:
    existing = Certificate.objects.filter(enrollment=enrollment).first()
    if existing is not None:
        return existing

    uid = secrets.token_hex(10)
    certificate = Certificate.objects.create(
        enrollment=enrollment,
        certificate_uid=uid,
        qr_payload=f"{settings.PUBLIC_APP_URL}/certificates/{uid}/verify",
    )
    ensure_certificate_pdf(certificate)
    return certificate
