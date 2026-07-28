from decimal import Decimal

import pytest

from apps.analytics.models import AnalyticsEvent
from apps.analytics.services import record_analytics_event
from apps.catalog.models import Course
from apps.content.models import Lesson, Section
from apps.learning.models import Enrollment

pytestmark = pytest.mark.django_db


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


@pytest.fixture
def student(django_user_model):
    return django_user_model.objects.create_user(email="student@example.com", password="x")


@pytest.fixture
def student_client(api_client, student):
    api_client.force_authenticate(user=student)
    return api_client


@pytest.fixture
def course(instructor):
    c = Course.objects.create(owner=instructor, title="Analytics Course", price_amount=Decimal("0"))
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


class TestRecordAnalyticsEvent:
    def test_creates_event_row(self, student, course):
        event = record_analytics_event("test.event", actor=student, course=course, payload={"x": 1})

        assert AnalyticsEvent.objects.filter(id=event.id, event_name="test.event").exists()
        assert event.payload == {"x": 1}


class TestEnrollmentIngestion:
    def test_enroll_records_analytics_event(self, student_client, course):
        response = student_client.post(
            "/api/v1/enrollments/", {"course_id": str(course.id)}, format="json"
        )

        assert response.status_code == 201
        assert AnalyticsEvent.objects.filter(
            event_name="enrollment.created", course=course
        ).exists()

    def test_progress_update_records_analytics_events(self, student_client, student, course):
        section = Section.objects.create(course=course, title="Section 1")
        lesson = Lesson.objects.create(section=section, title="Only Lesson")
        Enrollment.objects.create(student=student, course=course)

        response = student_client.post(
            "/api/v1/progress/",
            {"lesson_id": str(lesson.id), "percent_complete": 100, "last_position_seconds": 120},
            format="json",
        )

        assert response.status_code == 200
        assert AnalyticsEvent.objects.filter(event_name="lesson.progress", course=course).exists()
        assert AnalyticsEvent.objects.filter(
            event_name="enrollment.completed", course=course
        ).exists()
