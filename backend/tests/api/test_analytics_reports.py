from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.analytics import aggregation
from apps.analytics.models import (
    CourseCompletionAggregate,
    EngagementDailyAggregate,
    InstructorEarningsAggregate,
    LessonDropOffAggregate,
    LessonWatchTimeAggregate,
    RevenueDailyAggregate,
)
from apps.authorization.models import Role, UserRole
from apps.catalog.models import Course
from apps.commerce.models import Order, Payment
from apps.content.models import Lesson, Section
from apps.learning.models import Enrollment, ProgressTracking
from apps.payouts.models import Transaction, Wallet

pytestmark = pytest.mark.django_db


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


@pytest.fixture
def student(django_user_model):
    return django_user_model.objects.create_user(email="student@example.com", password="x")


@pytest.fixture
def finance_officer(django_user_model):
    user = django_user_model.objects.create_user(email="finance@example.com", password="x")
    UserRole.objects.create(user=user, role=Role.objects.get(code="finance_officer"))
    return user


@pytest.fixture
def finance_client(api_client, finance_officer):
    api_client.force_authenticate(user=finance_officer)
    return api_client


@pytest.fixture
def content_reviewer(django_user_model):
    user = django_user_model.objects.create_user(email="reviewer@example.com", password="x")
    UserRole.objects.create(user=user, role=Role.objects.get(code="content_reviewer"))
    return user


@pytest.fixture
def reviewer_client(api_client, content_reviewer):
    api_client.force_authenticate(user=content_reviewer)
    return api_client


@pytest.fixture
def student_client(api_client, student):
    api_client.force_authenticate(user=student)
    return api_client


@pytest.fixture
def course(instructor):
    c = Course.objects.create(
        owner=instructor, title="Analytics Course", price_amount=Decimal("100.00")
    )
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


TODAY = timezone.now().date()
YESTERDAY = TODAY - timedelta(days=1)


class TestAggregateRevenue:
    def test_sums_successful_payments_and_subtracts_refunds(self, student, course):
        order = Order.objects.create(buyer=student, total_amount=Decimal("100.00"), currency="USD")
        payment = Payment.objects.create(
            order=order,
            provider="stripe",
            status=Payment.STATUS_SUCCEEDED,
            amount=Decimal("100.00"),
            currency="USD",
            paid_at=timezone.now(),
        )
        from apps.commerce.models import Refund

        Refund.objects.create(
            payment=payment, amount=Decimal("20.00"), status=Refund.STATUS_SUCCEEDED
        )

        count = aggregation.aggregate_revenue(TODAY, TODAY + timedelta(days=1))

        assert count == 1
        row = RevenueDailyAggregate.objects.get(currency="USD")
        assert row.gross_amount == Decimal("100.00")
        assert row.net_amount == Decimal("80.00")


class TestAggregateEngagement:
    def test_counts_new_enrollments_and_active_students(self, student, course):
        Enrollment.objects.create(student=student, course=course)

        count = aggregation.aggregate_engagement(TODAY, TODAY + timedelta(days=1))

        assert count == 1
        row = EngagementDailyAggregate.objects.get(course=course)
        assert row.new_enrollments_count == 1


class TestAggregateCompletion:
    def test_cumulative_snapshot(self, student, course):
        Enrollment.objects.create(
            student=student,
            course=course,
            status=Enrollment.STATUS_COMPLETED,
            completed_at=timezone.now(),
        )

        count = aggregation.aggregate_completion(TODAY, TODAY + timedelta(days=1))

        assert count == 1
        row = CourseCompletionAggregate.objects.get(course=course)
        assert row.enrollments_count == 1
        assert row.completions_count == 1
        assert row.completion_rate == Decimal("100")


class TestAggregateWatchTimeAndDropOff:
    def test_watch_time_and_drop_off(self, student, course):
        section = Section.objects.create(course=course, title="S1")
        lesson = Lesson.objects.create(section=section, title="L1")
        enrollment = Enrollment.objects.create(student=student, course=course)
        ProgressTracking.objects.create(
            enrollment=enrollment, lesson=lesson, percent_complete=50, last_position_seconds=90
        )

        watch_count = aggregation.aggregate_watch_time(TODAY, TODAY + timedelta(days=1))
        drop_off_count = aggregation.aggregate_drop_off(TODAY, TODAY + timedelta(days=1))

        assert watch_count == 1
        assert drop_off_count == 1
        watch_row = LessonWatchTimeAggregate.objects.get(lesson=lesson)
        assert watch_row.total_watch_seconds == 90
        drop_row = LessonDropOffAggregate.objects.get(lesson=lesson)
        assert drop_row.started_count == 1
        assert drop_row.completed_count == 0
        assert drop_row.drop_off_rate == Decimal("100")


class TestAggregateInstructorEarnings:
    def test_sums_instructor_credit_transactions(self, instructor):
        wallet = Wallet.objects.create(
            owner_type=Wallet.OWNER_INSTRUCTOR, owner_id=instructor.id, currency="USD"
        )
        Transaction.objects.create(
            wallet=wallet,
            direction=Transaction.DIRECTION_CREDIT,
            amount=Decimal("70.00"),
            reason="course_sale",
        )

        count = aggregation.aggregate_instructor_earnings(TODAY, TODAY + timedelta(days=1))

        assert count == 1
        row = InstructorEarningsAggregate.objects.get(instructor=instructor)
        assert row.net_amount == Decimal("70.00")
        assert row.gross_amount == Decimal("70.00")


class TestReportEndpoints:
    def test_revenue_requires_finance_permission(self, student_client):
        response = student_client.get("/api/v1/analytics/revenue/")

        assert response.status_code == 403

    def test_finance_officer_can_view_revenue(self, finance_client):
        RevenueDailyAggregate.objects.create(
            period_start=YESTERDAY,
            period_end=TODAY,
            currency="USD",
            gross_amount=Decimal("100"),
            net_amount=Decimal("90"),
        )

        response = finance_client.get("/api/v1/analytics/revenue/")

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_content_reviewer_can_view_engagement_but_not_revenue(self, reviewer_client, course):
        EngagementDailyAggregate.objects.create(
            course=course, period_start=YESTERDAY, period_end=TODAY, active_students_count=3
        )

        engagement_response = reviewer_client.get("/api/v1/analytics/student-engagement/")
        revenue_response = reviewer_client.get("/api/v1/analytics/revenue/")

        assert engagement_response.status_code == 200
        assert revenue_response.status_code == 403

    def test_admin_report_alias_reuses_same_data(self, finance_client):
        RevenueDailyAggregate.objects.create(
            period_start=YESTERDAY,
            period_end=TODAY,
            currency="USD",
            gross_amount=Decimal("5"),
            net_amount=Decimal("5"),
        )

        canonical = finance_client.get("/api/v1/analytics/revenue/")
        alias = finance_client.get("/api/v1/admin/reports/revenue/")

        assert canonical.data == alias.data

    def test_course_performance_requires_course_id(self, reviewer_client):
        response = reviewer_client.get("/api/v1/analytics/course-performance/")

        assert response.status_code == 400

    def test_course_performance_returns_combined_snapshot(self, reviewer_client, course):
        CourseCompletionAggregate.objects.create(
            course=course,
            period_start=YESTERDAY,
            period_end=TODAY,
            enrollments_count=2,
            completions_count=1,
        )

        response = reviewer_client.get(
            "/api/v1/analytics/course-performance/", {"course_id": str(course.id)}
        )

        assert response.status_code == 200
        assert response.data["completion"]["enrollments_count"] == 2


class TestInstructorEarningsReport:
    def test_instructor_only_sees_own_earnings_no_id_param_exists(self, instructor, student):
        instructor_client_ = _client_for(instructor)
        InstructorEarningsAggregate.objects.create(
            instructor=instructor,
            period_start=YESTERDAY,
            period_end=TODAY,
            currency="USD",
            net_amount=Decimal("50"),
        )
        InstructorEarningsAggregate.objects.create(
            instructor=student,
            period_start=YESTERDAY,
            period_end=TODAY,
            currency="USD",
            net_amount=Decimal("999"),
        )

        response = instructor_client_.get("/api/v1/analytics/instructor-earnings/")

        assert len(response.data) == 1
        assert Decimal(response.data[0]["net_amount"]) == Decimal("50")

    def test_requires_authentication_only_no_special_role(self, instructor):
        response = _client_for(instructor).get("/api/v1/analytics/instructor-earnings/")

        assert response.status_code == 200


def _client_for(user):
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(user=user)
    return client
