import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="catalog.notify_course_update", time_limit=300)
def notify_course_update(course_id: str) -> None:
    """Fans out the "course updated" notification to every enrolled
    student. Run as a task, not inline in the PATCH/PUT request that
    triggers it — a popular course can have thousands of enrollments, and
    each notification is its own DB write plus a further Celery dispatch
    (see notifications.services.notify), so doing this synchronously would
    block the web worker for the entire fan-out before responding."""
    from .models import Course
    from .services import notify_enrolled_students_of_update

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        logger.warning("catalog.notify_course_update: course %s no longer exists", course_id)
        return
    notify_enrolled_students_of_update(course)
