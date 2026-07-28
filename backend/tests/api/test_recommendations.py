from decimal import Decimal

import pytest

from apps.catalog.models import Category, Course, CourseCategory
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


def _published_course(instructor, title, *, difficulty=Course.DIFFICULTY_BEGINNER, **kwargs):
    c = Course.objects.create(
        owner=instructor, title=title, difficulty=difficulty, price_amount=Decimal("10.00"), **kwargs
    )
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


@pytest.fixture
def category(instructor):
    return Category.objects.create(name="Data Science", slug="data-science")


class TestRecommendedCourses:
    def test_excludes_already_enrolled_courses(self, student_client, student, instructor, category):
        enrolled_course = _published_course(instructor, "Enrolled Course")
        CourseCategory.objects.create(course=enrolled_course, category=category)
        Enrollment.objects.create(student=student, course=enrolled_course)
        other_course = _published_course(instructor, "Other In Same Category")
        CourseCategory.objects.create(course=other_course, category=category)

        response = student_client.get("/api/v1/ai/recommendations/courses/")

        titles = [c["title"] for c in response.data]
        assert "Enrolled Course" not in titles
        assert "Other In Same Category" in titles

    def test_cold_start_falls_back_to_popular_courses(self, student_client, instructor):
        _published_course(instructor, "Popular Course")

        response = student_client.get("/api/v1/ai/recommendations/courses/")

        assert response.status_code == 200
        assert len(response.data) == 1


class TestLearningPaths:
    def test_orders_by_difficulty_then_popularity(self, student_client, student, instructor, category):
        anchor = _published_course(instructor, "Anchor Course")
        CourseCategory.objects.create(course=anchor, category=category)
        Enrollment.objects.create(student=student, course=anchor)

        advanced = _published_course(instructor, "Advanced One", difficulty=Course.DIFFICULTY_ADVANCED)
        CourseCategory.objects.create(course=advanced, category=category)
        beginner = _published_course(instructor, "Beginner One", difficulty=Course.DIFFICULTY_BEGINNER)
        CourseCategory.objects.create(course=beginner, category=category)

        response = student_client.get("/api/v1/ai/recommendations/learning-paths/")

        titles = [c["title"] for c in response.data]
        assert titles.index("Beginner One") < titles.index("Advanced One")


class TestCourseSearch:
    def test_requires_query_param(self, api_client):
        response = api_client.get("/api/v1/ai/search/")

        assert response.status_code == 400

    def test_matches_title_and_summary(self, api_client, instructor):
        _published_course(instructor, "Machine Learning Basics", summary="intro to ML")
        _published_course(instructor, "Cooking 101", summary="learn to cook")

        response = api_client.get("/api/v1/ai/search/", {"q": "machine"})

        titles = [c["title"] for c in response.data]
        assert titles == ["Machine Learning Basics"]

    def test_public_access(self, api_client, instructor):
        _published_course(instructor, "Public Course")

        response = api_client.get("/api/v1/ai/search/", {"q": "public"})

        assert response.status_code == 200
