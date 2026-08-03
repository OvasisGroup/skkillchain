from .models import Course


def notify_enrolled_students_of_update(course: Course) -> None:
    """Called after an instructor edits a course that's already live —
    enrollments only ever exist against a published course (see
    learning.views.EnrollView), so this is a no-op for a draft/rejected
    edit where nobody could be enrolled yet."""
    from apps.identity.models import User
    from apps.learning.models import Enrollment
    from apps.notifications.services import notify

    student_ids = (
        Enrollment.objects.filter(course=course).values_list("student_id", flat=True).distinct()
    )
    for student in User.objects.filter(id__in=student_ids):
        notify(
            student,
            type="course_update",
            channels=["in_app", "email"],
            title=f"Course updated: {course.title}",
            body=f'Your instructor made updates to "{course.title}". Check out what\'s new.',
        )
