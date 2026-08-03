import pytest

from apps.catalog.models import Category, Course
from apps.content.models import Section

pytestmark = pytest.mark.django_db


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


@pytest.fixture
def category():
    return Category.objects.create(name="Programming", slug="programming")


@pytest.fixture
def other_instructor(django_user_model):
    return django_user_model.objects.create_user(email="other-instructor@example.com", password="x")


@pytest.fixture
def auth_client(api_client, instructor):
    api_client.force_authenticate(user=instructor)
    return api_client


class TestCourseCreate:
    def test_create_course_as_draft(self, auth_client, instructor, category):
        response = auth_client.post(
            "/api/v1/instructor/courses/",
            {
                "title": "New Course",
                "summary": "A great course",
                "difficulty": "beginner",
                "category_id": str(category.id),
            },
            format="json",
        )

        assert response.status_code == 201
        # The create response is what the client uses for every subsequent
        # call (add sections, submit for review, ...) — a response missing
        # "id" is a real bug even though the DB row itself is correct.
        assert response.data["id"] is not None
        course = Course.objects.get(title="New Course")
        assert str(course.id) == str(response.data["id"])
        assert course.owner_id == instructor.id
        assert course.status == Course.STATUS_DRAFT
        assert course.category_id == category.id

    def test_create_requires_authentication(self, api_client):
        response = api_client.post("/api/v1/instructor/courses/", {"title": "X"}, format="json")

        assert response.status_code == 401

    def test_create_requires_category(self, auth_client):
        response = auth_client.post(
            "/api/v1/instructor/courses/", {"title": "No Category"}, format="json"
        )

        assert response.status_code == 400
        assert "category_id" in response.data["errors"]

    def test_list_only_shows_own_courses(self, auth_client, instructor, other_instructor):
        Course.objects.create(owner=instructor, title="Mine")
        Course.objects.create(owner=other_instructor, title="Not Mine")

        response = auth_client.get("/api/v1/instructor/courses/")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == ["Mine"]


class TestCourseUpdate:
    def test_owner_can_edit_draft(self, auth_client, instructor):
        course = Course.objects.create(owner=instructor, title="Draft Course")

        response = auth_client.patch(
            f"/api/v1/instructor/courses/{course.id}/",
            {"summary": "Updated summary"},
            format="json",
        )

        assert response.status_code == 200
        course.refresh_from_db()
        assert course.summary == "Updated summary"

    def test_non_owner_cannot_see_or_edit(self, api_client, instructor, other_instructor):
        course = Course.objects.create(owner=instructor, title="Draft Course")
        api_client.force_authenticate(user=other_instructor)

        response = api_client.patch(
            f"/api/v1/instructor/courses/{course.id}/", {"summary": "Hacked"}, format="json"
        )

        assert response.status_code == 404  # filtered out of the owner-scoped queryset entirely

    def test_cannot_edit_a_submitted_course(self, auth_client, instructor):
        course = Course.objects.create(owner=instructor, title="Submitted Course")
        course.submit_for_review()

        response = auth_client.patch(
            f"/api/v1/instructor/courses/{course.id}/", {"summary": "Sneaky edit"}, format="json"
        )

        assert response.status_code == 400

    def test_owner_can_edit_published_course(self, auth_client, instructor):
        course = Course.objects.create(owner=instructor, title="Live Course")
        course.status = Course.STATUS_PUBLISHED
        course.save(update_fields=["status"])

        response = auth_client.patch(
            f"/api/v1/instructor/courses/{course.id}/",
            {"summary": "Refreshed summary"},
            format="json",
        )

        assert response.status_code == 200
        course.refresh_from_db()
        assert course.summary == "Refreshed summary"

    def test_editing_published_course_notifies_enrolled_students(
        self, auth_client, instructor, django_user_model, monkeypatch
    ):
        from apps.catalog import tasks
        from apps.learning.models import Enrollment
        from apps.notifications.models import Notification

        course = Course.objects.create(owner=instructor, title="Live Course")
        course.status = Course.STATUS_PUBLISHED
        course.save(update_fields=["status"])
        student = django_user_model.objects.create_user(email="student@example.com", password="x")
        Enrollment.objects.create(student=student, course=course)

        # The fan-out runs as a Celery task (see catalog/tasks.py) rather than
        # inline in the request, so a popular course's edit doesn't block the
        # web worker for every enrolled student's notification. Run it
        # synchronously here, same as tests/api/test_ai_generation.py does for
        # its own dispatch task, to verify the fan-out logic itself.
        monkeypatch.setattr(tasks.notify_course_update, "delay", tasks.notify_course_update)

        response = auth_client.patch(
            f"/api/v1/instructor/courses/{course.id}/",
            {"summary": "New and improved"},
            format="json",
        )

        assert response.status_code == 200
        assert Notification.objects.filter(user=student, type="course_update").exists()

    def test_editing_draft_course_sends_no_notifications(self, auth_client, instructor):
        from apps.notifications.models import Notification

        course = Course.objects.create(owner=instructor, title="Still a Draft")

        response = auth_client.patch(
            f"/api/v1/instructor/courses/{course.id}/", {"summary": "Tweak"}, format="json"
        )

        assert response.status_code == 200
        assert not Notification.objects.filter(type="course_update").exists()


class TestApprovalWorkflow:
    def test_full_happy_path(self, auth_client, instructor, django_user_model):
        from apps.authorization.models import Role, UserRole

        course = Course.objects.create(owner=instructor, title="End to End")

        submit = auth_client.post(f"/api/v1/instructor/courses/{course.id}/submit-review/")
        assert submit.status_code == 200
        assert submit.data["status"] == "submitted"

        reviewer = django_user_model.objects.create_user(email="reviewer@example.com", password="x")
        UserRole.objects.create(user=reviewer, role=Role.objects.get(code="content_reviewer"))
        reviewer_client = auth_client.__class__()
        reviewer_client.force_authenticate(user=reviewer)

        approve = reviewer_client.post(f"/api/v1/admin/courses/{course.id}/approve/")
        assert approve.status_code == 200
        assert approve.data["status"] == "approved"

        publish = auth_client.post(f"/api/v1/instructor/courses/{course.id}/publish/")
        assert publish.status_code == 200
        assert publish.data["status"] == "published"

    def test_cannot_publish_before_approval(self, auth_client, instructor):
        course = Course.objects.create(owner=instructor, title="Too Fast")

        response = auth_client.post(f"/api/v1/instructor/courses/{course.id}/publish/")

        assert response.status_code == 400

    def test_only_owner_can_submit(self, api_client, instructor, other_instructor):
        course = Course.objects.create(owner=instructor, title="Not Yours")
        api_client.force_authenticate(user=other_instructor)

        response = api_client.post(f"/api/v1/instructor/courses/{course.id}/submit-review/")

        assert response.status_code == 403

    def test_approve_requires_permission(self, auth_client, instructor):
        course = Course.objects.create(owner=instructor, title="Needs Review")
        course.submit_for_review()

        response = auth_client.post(f"/api/v1/admin/courses/{course.id}/approve/")

        assert response.status_code == 403

    def test_reject_requires_reason(self, api_client, instructor, django_user_model):
        from apps.authorization.models import Role, UserRole

        course = Course.objects.create(owner=instructor, title="Needs Fixes")
        course.submit_for_review()

        reviewer = django_user_model.objects.create_user(
            email="reviewer2@example.com", password="x"
        )
        UserRole.objects.create(user=reviewer, role=Role.objects.get(code="content_reviewer"))
        api_client.force_authenticate(user=reviewer)

        missing_reason = api_client.post(
            f"/api/v1/admin/courses/{course.id}/reject/", {}, format="json"
        )
        assert missing_reason.status_code == 400

        with_reason = api_client.post(
            f"/api/v1/admin/courses/{course.id}/reject/",
            {"reason": "Needs captions"},
            format="json",
        )
        assert with_reason.status_code == 200
        course.refresh_from_db()
        assert course.status == Course.STATUS_REJECTED
        assert course.rejection_reason == "Needs captions"

    def test_pending_review_list_requires_permission(self, auth_client):
        response = auth_client.get("/api/v1/admin/courses/pending-review/")

        assert response.status_code == 403


class TestSectionAndLessonAuthoring:
    def test_owner_can_add_section_and_lesson(self, auth_client, instructor):
        course = Course.objects.create(owner=instructor, title="With Sections")

        section_response = auth_client.post(
            f"/api/v1/instructor/courses/{course.id}/sections/",
            {"title": "Intro", "sort_order": 1},
            format="json",
        )
        assert section_response.status_code == 201
        section_id = section_response.data["id"]

        lesson_response = auth_client.post(
            f"/api/v1/instructor/sections/{section_id}/lessons/",
            {"title": "Welcome", "lesson_type": "video", "sort_order": 1},
            format="json",
        )
        assert lesson_response.status_code == 201

    def test_non_owner_cannot_add_section(self, api_client, instructor, other_instructor):
        course = Course.objects.create(owner=instructor, title="Not Yours")
        api_client.force_authenticate(user=other_instructor)

        response = api_client.post(
            f"/api/v1/instructor/courses/{course.id}/sections/",
            {"title": "Intruding"},
            format="json",
        )

        assert response.status_code == 403

    def test_non_owner_cannot_list_sections(self, api_client, instructor, other_instructor):
        # IDOR check: get_queryset() must ownership-gate the list path too,
        # not just perform_create() — a course's curriculum structure
        # (including unpublished/draft courses CourseDetailView otherwise
        # hides) must not be enumerable by any authenticated user.
        course = Course.objects.create(owner=instructor, title="Not Yours")
        Section.objects.create(course=course, title="Secret Section")
        api_client.force_authenticate(user=other_instructor)

        response = api_client.get(f"/api/v1/instructor/courses/{course.id}/sections/")

        assert response.status_code == 403

    def test_non_owner_cannot_list_lessons(self, api_client, instructor, other_instructor):
        from apps.content.models import Lesson

        course = Course.objects.create(owner=instructor, title="Not Yours Either")
        section = Section.objects.create(course=course, title="Section")
        Lesson.objects.create(section=section, title="Secret Lesson")
        api_client.force_authenticate(user=other_instructor)

        response = api_client.get(f"/api/v1/instructor/sections/{section.id}/lessons/")

        assert response.status_code == 403

    def test_cannot_add_section_once_submitted(self, auth_client, instructor):
        course = Course.objects.create(owner=instructor, title="Locked")
        course.submit_for_review()

        response = auth_client.post(
            f"/api/v1/instructor/courses/{course.id}/sections/",
            {"title": "Too Late"},
            format="json",
        )

        assert response.status_code == 400
        assert Section.objects.filter(course=course).count() == 0
