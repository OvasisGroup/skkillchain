import pytest

from apps.catalog.models import Course
from apps.content.models import Lesson, Section
from apps.learning.models import Certificate, Enrollment, ProgressTracking
from apps.learning.services import issue_certificate, maybe_complete_enrollment

pytestmark = pytest.mark.django_db


@pytest.fixture
def course_with_two_lessons(django_user_model):
    instructor = django_user_model.objects.create_user(email="instructor@example.com", password="x")
    course = Course.objects.create(owner=instructor, title="Two Lesson Course")
    course.status = Course.STATUS_PUBLISHED
    course.save(update_fields=["status"])
    section = Section.objects.create(course=course, title="Only Section")
    lesson_a = Lesson.objects.create(section=section, title="Lesson A", sort_order=1)
    lesson_b = Lesson.objects.create(section=section, title="Lesson B", sort_order=2)
    return course, lesson_a, lesson_b


@pytest.fixture
def enrollment(course_with_two_lessons, django_user_model):
    course, _, _ = course_with_two_lessons
    student = django_user_model.objects.create_user(email="student@example.com", password="x")
    return Enrollment.objects.create(course=course, student=student)


class TestMaybeCompleteEnrollment:
    def test_not_completed_with_partial_progress(self, course_with_two_lessons, enrollment):
        _, lesson_a, _ = course_with_two_lessons
        ProgressTracking.objects.create(
            enrollment=enrollment, lesson=lesson_a, percent_complete=100
        )

        certificate = maybe_complete_enrollment(enrollment)

        assert certificate is None
        enrollment.refresh_from_db()
        assert enrollment.status == Enrollment.STATUS_ACTIVE

    def test_completes_and_issues_certificate_once_all_lessons_done(
        self, course_with_two_lessons, enrollment
    ):
        _, lesson_a, lesson_b = course_with_two_lessons
        ProgressTracking.objects.create(
            enrollment=enrollment, lesson=lesson_a, percent_complete=100
        )
        ProgressTracking.objects.create(
            enrollment=enrollment, lesson=lesson_b, percent_complete=100
        )

        certificate = maybe_complete_enrollment(enrollment)

        assert certificate is not None
        enrollment.refresh_from_db()
        assert enrollment.status == Enrollment.STATUS_COMPLETED
        assert enrollment.completed_at is not None

    def test_partial_progress_on_a_lesson_does_not_complete(
        self, course_with_two_lessons, enrollment
    ):
        _, lesson_a, lesson_b = course_with_two_lessons
        ProgressTracking.objects.create(
            enrollment=enrollment, lesson=lesson_a, percent_complete=100
        )
        ProgressTracking.objects.create(enrollment=enrollment, lesson=lesson_b, percent_complete=80)

        certificate = maybe_complete_enrollment(enrollment)

        assert certificate is None

    def test_already_completed_enrollment_is_a_noop(self, course_with_two_lessons, enrollment):
        _, lesson_a, lesson_b = course_with_two_lessons
        ProgressTracking.objects.create(
            enrollment=enrollment, lesson=lesson_a, percent_complete=100
        )
        ProgressTracking.objects.create(
            enrollment=enrollment, lesson=lesson_b, percent_complete=100
        )
        maybe_complete_enrollment(enrollment)

        second_call = maybe_complete_enrollment(enrollment)

        assert second_call is None


class TestIssueCertificate:
    def test_issuing_twice_returns_the_same_certificate(self, enrollment):
        first = issue_certificate(enrollment)
        second = issue_certificate(enrollment)

        assert first.id == second.id
        assert Certificate.objects.filter(enrollment=enrollment).count() == 1

    def test_qr_payload_points_at_public_app_url(self, enrollment, settings):
        settings.PUBLIC_APP_URL = "https://skillchain.example"

        certificate = issue_certificate(enrollment)

        assert (
            certificate.qr_payload
            == f"https://skillchain.example/certificates/{certificate.certificate_uid}/verify"
        )
