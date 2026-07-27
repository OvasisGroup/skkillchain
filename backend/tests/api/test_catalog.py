import pytest

from apps.catalog.models import Category, Course
from apps.content.models import Lesson, Section

pytestmark = pytest.mark.django_db


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


def _published_course(instructor, **kwargs):
    course = Course.objects.create(
        owner=instructor, title=kwargs.pop("title", "Published Course"), **kwargs
    )
    course.status = Course.STATUS_PUBLISHED
    course.save(update_fields=["status"])
    return course


class TestCourseListView:
    def test_lists_only_published_courses(self, api_client, instructor):
        _published_course(instructor, title="Live Course")
        Course.objects.create(owner=instructor, title="Still a Draft")

        response = api_client.get("/api/v1/courses/")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == ["Live Course"]

    def test_filters_by_difficulty(self, api_client, instructor):
        _published_course(instructor, title="Easy", difficulty=Course.DIFFICULTY_BEGINNER)
        _published_course(instructor, title="Hard", difficulty=Course.DIFFICULTY_ADVANCED)

        response = api_client.get("/api/v1/courses/?difficulty=advanced")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == ["Hard"]

    def test_filters_by_category(self, api_client, instructor):
        cat = Category.objects.create(name="Data Science", slug="data-science")
        matching = _published_course(instructor, title="ML 101")
        matching.categories.add(cat)
        _published_course(instructor, title="Unrelated")

        response = api_client.get("/api/v1/courses/?category=data-science")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == ["ML 101"]


class TestCourseDetailView:
    def test_published_course_visible_to_anyone(self, api_client, instructor):
        course = _published_course(instructor)

        response = api_client.get(f"/api/v1/courses/{course.id}/")

        assert response.status_code == 200
        assert response.data["title"] == course.title

    def test_draft_course_hidden_from_public(self, api_client, instructor):
        course = Course.objects.create(owner=instructor, title="Secret Draft")

        response = api_client.get(f"/api/v1/courses/{course.id}/")

        assert response.status_code == 404

    def test_draft_course_visible_to_owner(self, api_client, instructor):
        course = Course.objects.create(owner=instructor, title="My Draft")
        api_client.force_authenticate(user=instructor)

        response = api_client.get(f"/api/v1/courses/{course.id}/")

        assert response.status_code == 200

    def test_draft_course_hidden_from_other_authenticated_user(
        self, api_client, instructor, django_user_model
    ):
        course = Course.objects.create(owner=instructor, title="Not Yours")
        other = django_user_model.objects.create_user(email="other@example.com", password="x")
        api_client.force_authenticate(user=other)

        response = api_client.get(f"/api/v1/courses/{course.id}/")

        assert response.status_code == 404


class TestCoursePreviewView:
    def test_returns_only_preview_flagged_lessons(self, api_client, instructor):
        course = _published_course(instructor)
        section = Section.objects.create(course=course, title="Getting Started")
        Lesson.objects.create(section=section, title="Intro (free)", is_preview=True)
        Lesson.objects.create(section=section, title="Paid content", is_preview=False)

        response = api_client.get(f"/api/v1/courses/{course.id}/preview/")

        assert response.status_code == 200
        lesson_titles = [lesson["title"] for entry in response.data for lesson in entry["lessons"]]
        assert lesson_titles == ["Intro (free)"]


class TestCategoryAndTagLists:
    def test_category_list(self, api_client):
        Category.objects.create(name="Design", slug="design")

        response = api_client.get("/api/v1/categories/")

        assert response.status_code == 200
        assert any(item["slug"] == "design" for item in response.data)
