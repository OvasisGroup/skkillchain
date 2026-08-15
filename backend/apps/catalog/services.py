from .models import Course


def notify_enrolled_students(course: Course, subject: str, message: str) -> None:
    """Fans out an in-app + email notification to every student enrolled in
    `course`. Enrollments only ever exist against a published course (see
    learning.views.EnrollView), so this is a no-op for a draft/rejected
    course where nobody could be enrolled yet."""
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
            title=subject,
            body=message,
        )


def notify_enrolled_students_of_update(course: Course) -> None:
    """Called after an instructor (or an admin, via AdminCourseDetailView)
    edits a course that's already live."""
    notify_enrolled_students(
        course,
        subject=f"Course updated: {course.title}",
        message=f'Your instructor made updates to "{course.title}". Check out what\'s new.',
    )
