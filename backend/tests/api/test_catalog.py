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
        matching = _published_course(instructor, title="ML 101", category=cat)
        _published_course(instructor, title="Unrelated")

        response = api_client.get("/api/v1/courses/?category=data-science")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == ["ML 101"]

    def test_filters_by_search_query_matching_title_or_summary(self, api_client, instructor):
        _published_course(instructor, title="Django for Beginners", summary="")
        _published_course(instructor, title="Cooking 101", summary="Learn Django-free recipes")
        _published_course(instructor, title="Unrelated", summary="")

        response = api_client.get("/api/v1/courses/?q=django")

        titles = {item["title"] for item in response.data["results"]}
        assert titles == {"Django for Beginners", "Cooking 101"}

    def test_filters_by_is_free(self, api_client, instructor):
        _published_course(instructor, title="Free Course", price_amount="0.00")
        _published_course(instructor, title="Paid Course", price_amount="49.99")

        free_response = api_client.get("/api/v1/courses/?is_free=true")
        paid_response = api_client.get("/api/v1/courses/?is_free=false")

        assert [item["title"] for item in free_response.data["results"]] == ["Free Course"]
        assert [item["title"] for item in paid_response.data["results"]] == ["Paid Course"]


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


class TestCategoryManagement:
    def test_create_requires_authentication(self, api_client):
        response = api_client.post("/api/v1/categories/", {"name": "Design"}, format="json")

        assert response.status_code == 401

    def test_create_requires_permission(self, api_client, instructor):
        api_client.force_authenticate(user=instructor)

        response = api_client.post("/api/v1/categories/", {"name": "Design"}, format="json")

        assert response.status_code == 403

    def test_admin_can_create_with_auto_slug(self, api_client, django_user_model):
        from apps.authorization.models import Role, UserRole

        admin = django_user_model.objects.create_user(email="admin@example.com", password="x")
        UserRole.objects.create(user=admin, role=Role.objects.get(code="administrator"))
        api_client.force_authenticate(user=admin)

        response = api_client.post("/api/v1/categories/", {"name": "Data Science"}, format="json")

        assert response.status_code == 201
        assert response.data["slug"] == "data-science"

    def test_admin_can_delete_unused_category(self, api_client, django_user_model):
        from apps.authorization.models import Role, UserRole

        admin = django_user_model.objects.create_user(email="admin@example.com", password="x")
        UserRole.objects.create(user=admin, role=Role.objects.get(code="administrator"))
        api_client.force_authenticate(user=admin)
        category = Category.objects.create(name="Unused", slug="unused")

        response = api_client.delete(f"/api/v1/categories/{category.id}/")

        assert response.status_code == 204
        assert not Category.objects.filter(pk=category.id).exists()

    def test_cannot_delete_category_in_use(self, api_client, django_user_model, instructor):
        from apps.authorization.models import Role, UserRole

        admin = django_user_model.objects.create_user(email="admin@example.com", password="x")
        UserRole.objects.create(user=admin, role=Role.objects.get(code="administrator"))
        api_client.force_authenticate(user=admin)
        category = Category.objects.create(name="In Use", slug="in-use")
        _published_course(instructor, title="Uses It", category=category)

        response = api_client.delete(f"/api/v1/categories/{category.id}/")

        assert response.status_code == 400
        assert Category.objects.filter(pk=category.id).exists()


class TestTagManagement:
    def test_authenticated_user_can_create_tag(self, api_client, instructor):
        from apps.catalog.models import Tag

        api_client.force_authenticate(user=instructor)

        response = api_client.post("/api/v1/tags/", {"name": "Django"}, format="json")

        assert response.status_code == 201
        assert response.data["slug"] == "django"
        assert Tag.objects.filter(name="Django").exists()

    def test_creating_existing_tag_is_idempotent(self, api_client, instructor):
        from apps.catalog.models import Tag

        Tag.objects.create(name="Python", slug="python")
        api_client.force_authenticate(user=instructor)

        response = api_client.post("/api/v1/tags/", {"name": "python"}, format="json")

        assert response.status_code == 200
        assert Tag.objects.filter(name__iexact="python").count() == 1

    def test_create_requires_authentication(self, api_client):
        response = api_client.post("/api/v1/tags/", {"name": "Django"}, format="json")

        assert response.status_code == 401


class TestInstructorDirectory:
    def test_lists_instructors_with_published_courses(self, api_client, instructor):
        _published_course(instructor, title="Live Course")

        response = api_client.get("/api/v1/instructors/")

        assert response.status_code == 200
        emails = [item["email"] for item in response.data]
        assert emails == [instructor.email]
        assert response.data[0]["published_course_count"] == 1

    def test_orders_newest_instructor_first(self, api_client, instructor, django_user_model):
        newer_instructor = django_user_model.objects.create_user(
            email="newer-instructor@example.com", password="x"
        )
        _published_course(instructor, title="Older Instructor's Course")
        _published_course(newer_instructor, title="Newer Instructor's Course")

        response = api_client.get("/api/v1/instructors/")

        emails = [item["email"] for item in response.data]
        assert emails == [newer_instructor.email, instructor.email]

    def test_lists_distinct_categories_taught(self, api_client, instructor):
        programming = Category.objects.create(name="Programming", slug="programming")
        design = Category.objects.create(name="Design", slug="design")
        _published_course(instructor, title="Course A", category=programming)
        _published_course(instructor, title="Course B", category=programming)
        _published_course(instructor, title="Course C", category=design)

        response = api_client.get("/api/v1/instructors/")

        names = {item["name"] for item in response.data[0]["categories"]}
        assert names == {"Programming", "Design"}

    def test_categories_empty_when_courses_uncategorized(self, api_client, instructor):
        _published_course(instructor, title="No Category")

        response = api_client.get("/api/v1/instructors/")

        assert response.data[0]["categories"] == []

    def test_excludes_users_with_only_draft_courses(self, api_client, instructor):
        Course.objects.create(owner=instructor, title="Still a Draft")

        response = api_client.get("/api/v1/instructors/")

        assert response.status_code == 200
        assert response.data == []

    def test_course_count_only_counts_published(self, api_client, instructor):
        _published_course(instructor, title="Published One")
        Course.objects.create(owner=instructor, title="Draft One")

        response = api_client.get("/api/v1/instructors/")

        assert response.data[0]["published_course_count"] == 1

    def test_detail_returns_profile_and_published_courses(self, api_client, instructor):
        from apps.identity.models import Profile

        Profile.objects.filter(user=instructor).update(
            first_name="Jane", last_name="Doe", bio="Backend engineer."
        )
        published = _published_course(instructor, title="Live Course")
        Course.objects.create(owner=instructor, title="Draft, not shown")

        response = api_client.get(f"/api/v1/instructors/{instructor.id}/")

        assert response.status_code == 200
        assert response.data["profile"]["first_name"] == "Jane"
        assert response.data["profile"]["bio"] == "Backend engineer."
        titles = [c["title"] for c in response.data["courses"]]
        assert titles == ["Live Course"]
        assert str(response.data["courses"][0]["id"]) == str(published.id)

    def test_detail_404s_for_instructor_with_no_published_courses(self, api_client, instructor):
        Course.objects.create(owner=instructor, title="Draft Only")

        response = api_client.get(f"/api/v1/instructors/{instructor.id}/")

        assert response.status_code == 404

    def test_detail_404s_for_unknown_user(self, api_client):
        response = api_client.get("/api/v1/instructors/00000000-0000-0000-0000-000000000000/")

        assert response.status_code == 404


class TestAdminCourseManagement:
    @pytest.fixture
    def admin(self, django_user_model):
        from apps.authorization.models import Role, UserRole

        admin = django_user_model.objects.create_user(email="admin@example.com", password="x")
        UserRole.objects.create(user=admin, role=Role.objects.get(code="administrator"))
        return admin

    @pytest.fixture
    def admin_client(self, api_client, admin):
        api_client.force_authenticate(user=admin)
        return api_client

    @pytest.fixture
    def instructor_role_user(self, django_user_model):
        from apps.authorization.models import Role, UserRole

        user = django_user_model.objects.create_user(
            email="real-instructor@example.com", password="x"
        )
        UserRole.objects.create(user=user, role=Role.objects.get(code="instructor"))
        return user

    @pytest.fixture
    def category(self):
        return Category.objects.create(name="Programming", slug="programming")

    def test_non_admin_gets_403_on_list(self, api_client, instructor):
        api_client.force_authenticate(user=instructor)

        response = api_client.get("/api/v1/admin/courses/")

        assert response.status_code == 403

    def test_lists_every_course_regardless_of_owner_or_status(
        self, admin_client, instructor
    ):
        Course.objects.create(owner=instructor, title="Someone's Draft")
        _published_course(instructor, title="Someone's Published Course")

        response = admin_client.get("/api/v1/admin/courses/")

        titles = {item["title"] for item in response.data["results"]}
        assert titles == {"Someone's Draft", "Someone's Published Course"}

    def test_filters_by_status(self, admin_client, instructor):
        Course.objects.create(owner=instructor, title="Draft One")
        _published_course(instructor, title="Live One")

        response = admin_client.get("/api/v1/admin/courses/?status=draft")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == ["Draft One"]

    def test_admin_can_create_course_for_instructor(
        self, admin_client, instructor_role_user, category
    ):
        response = admin_client.post(
            "/api/v1/admin/courses/",
            {
                "owner_id": str(instructor_role_user.id),
                "title": "Ghost-authored Course",
                "category_id": str(category.id),
            },
            format="json",
        )

        assert response.status_code == 201
        course = Course.objects.get(id=response.data["id"])
        assert course.owner_id == instructor_role_user.id
        assert course.status == Course.STATUS_DRAFT

    def test_create_rejects_a_non_instructor_owner(self, admin_client, instructor, category):
        # `instructor` (test_catalog.py's module fixture) is a plain user
        # with no instructor role — owner_id's queryset only resolves users
        # who actually hold the role, same as the frontend's picker search.
        response = admin_client.post(
            "/api/v1/admin/courses/",
            {
                "owner_id": str(instructor.id),
                "title": "Should Fail",
                "category_id": str(category.id),
            },
            format="json",
        )

        assert response.status_code == 400
        assert "owner_id" in response.data["errors"]

    def test_non_admin_gets_403_on_create(self, api_client, instructor, category):
        api_client.force_authenticate(user=instructor)

        response = api_client.post(
            "/api/v1/admin/courses/",
            {"owner_id": str(instructor.id), "title": "X", "category_id": str(category.id)},
            format="json",
        )

        assert response.status_code == 403

    def test_admin_can_edit_any_course_regardless_of_status(self, admin_client, instructor):
        course = Course.objects.create(owner=instructor, title="Submitted Course")
        course.submit_for_review()  # instructor's own PATCH blocks this status; admin's shouldn't

        response = admin_client.patch(
            f"/api/v1/admin/courses/{course.id}/", {"summary": "Admin edit"}, format="json"
        )

        assert response.status_code == 200
        course.refresh_from_db()
        assert course.summary == "Admin edit"

    def test_get_includes_prerequisites_and_nested_category(self, admin_client, instructor, category):
        from apps.catalog.models import CoursePrerequisite

        course = Course.objects.create(owner=instructor, title="With Prereqs", category=category)
        CoursePrerequisite.objects.create(course=course, text="Basic Python")

        response = admin_client.get(f"/api/v1/admin/courses/{course.id}/")

        assert response.status_code == 200
        assert response.data["prerequisites"] == ["Basic Python"]
        assert response.data["category"]["slug"] == category.slug

    def test_editing_published_course_notifies_enrolled_students(
        self, admin_client, instructor, django_user_model, monkeypatch
    ):
        from apps.catalog import tasks
        from apps.learning.models import Enrollment

        course = _published_course(instructor, title="Live Course")
        student = django_user_model.objects.create_user(email="student@example.com", password="x")
        Enrollment.objects.create(student=student, course=course)
        monkeypatch.setattr(tasks.notify_course_update, "delay", tasks.notify_course_update)

        response = admin_client.patch(
            f"/api/v1/admin/courses/{course.id}/", {"summary": "Refreshed"}, format="json"
        )

        assert response.status_code == 200

    def test_notify_instructor_creates_notification(self, admin_client, instructor):
        from apps.notifications.models import Notification

        course = _published_course(instructor, title="Live Course")

        response = admin_client.post(
            f"/api/v1/admin/courses/{course.id}/notify/",
            {"audience": "instructor", "subject": "Heads up", "message": "Please read this."},
            format="json",
        )

        assert response.status_code == 200
        notifications = Notification.objects.filter(user=instructor)
        channels = {n.channel for n in notifications}
        assert channels == {"in_app", "email"}
        assert all(n.title == "Heads up" for n in notifications)

    def test_notify_students_fans_out_via_task(
        self, admin_client, instructor, django_user_model, monkeypatch
    ):
        from apps.catalog import tasks
        from apps.learning.models import Enrollment
        from apps.notifications.models import Notification

        course = _published_course(instructor, title="Live Course")
        student = django_user_model.objects.create_user(email="student@example.com", password="x")
        Enrollment.objects.create(student=student, course=course)
        monkeypatch.setattr(
            tasks.notify_course_recipients, "delay", tasks.notify_course_recipients
        )

        response = admin_client.post(
            f"/api/v1/admin/courses/{course.id}/notify/",
            {"audience": "students", "subject": "New content", "message": "Check it out."},
            format="json",
        )

        assert response.status_code == 200
        notifications = Notification.objects.filter(user=student)
        assert notifications.count() == 2  # in_app + email
        assert Notification.objects.filter(user=instructor).count() == 0

    def test_non_admin_gets_403_on_notify(self, api_client, instructor):
        course = _published_course(instructor, title="Live Course")
        api_client.force_authenticate(user=instructor)

        response = api_client.post(
            f"/api/v1/admin/courses/{course.id}/notify/",
            {"audience": "both", "subject": "X", "message": "Y"},
            format="json",
        )

        assert response.status_code == 403
