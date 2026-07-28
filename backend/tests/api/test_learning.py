import pytest

from apps.catalog.models import Course
from apps.content.models import Lesson, Section
from apps.learning.models import Enrollment

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "a-strong-password-1"


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


@pytest.fixture
def published_course(instructor):
    course = Course.objects.create(owner=instructor, title="Published Course")
    course.status = Course.STATUS_PUBLISHED
    course.save(update_fields=["status"])
    return course


@pytest.fixture
def draft_course(instructor):
    return Course.objects.create(owner=instructor, title="Still a Draft")


@pytest.fixture
def two_lessons(published_course):
    section = Section.objects.create(course=published_course, title="Section")
    lesson_a = Lesson.objects.create(section=section, title="Lesson A", sort_order=1)
    lesson_b = Lesson.objects.create(section=section, title="Lesson B", sort_order=2)
    return lesson_a, lesson_b


@pytest.fixture
def student(django_user_model):
    return django_user_model.objects.create_user(email="student@example.com", password="x")


@pytest.fixture
def student_client(api_client, student):
    api_client.force_authenticate(user=student)
    return api_client


class TestEnroll:
    def test_enroll_in_published_course(self, student_client, published_course, student):
        response = student_client.post(
            "/api/v1/enrollments/", {"course_id": str(published_course.id)}, format="json"
        )

        assert response.status_code == 201
        assert Enrollment.objects.filter(student=student, course=published_course).exists()

    def test_cannot_enroll_twice(self, student_client, published_course):
        student_client.post(
            "/api/v1/enrollments/", {"course_id": str(published_course.id)}, format="json"
        )

        response = student_client.post(
            "/api/v1/enrollments/", {"course_id": str(published_course.id)}, format="json"
        )

        assert response.status_code == 400

    def test_cannot_enroll_in_a_draft_course(self, student_client, draft_course):
        response = student_client.post(
            "/api/v1/enrollments/", {"course_id": str(draft_course.id)}, format="json"
        )

        assert response.status_code == 404

    def test_enroll_requires_authentication(self, api_client, published_course):
        response = api_client.post(
            "/api/v1/enrollments/", {"course_id": str(published_course.id)}, format="json"
        )

        assert response.status_code == 401


class TestMyCoursesAndContinueLearning:
    def test_my_courses_lists_own_enrollments_only(
        self, student_client, published_course, django_user_model
    ):
        other = django_user_model.objects.create_user(email="other@example.com", password="x")
        Enrollment.objects.create(student=other, course=published_course)
        student_client.post(
            "/api/v1/enrollments/", {"course_id": str(published_course.id)}, format="json"
        )

        response = student_client.get("/api/v1/students/me/courses/")

        assert len(response.data["results"]) == 1

    def test_continue_learning_excludes_completed(
        self, student_client, student, published_course, two_lessons
    ):
        enrollment = Enrollment.objects.create(student=student, course=published_course)
        enrollment.status = Enrollment.STATUS_COMPLETED
        enrollment.save(update_fields=["status"])

        response = student_client.get("/api/v1/students/me/continue-learning/")

        assert response.data == []


class TestProgressAndCompletion:
    def test_progress_update_requires_enrollment(self, student_client, two_lessons):
        lesson_a, _ = two_lessons

        response = student_client.post(
            "/api/v1/progress/",
            {"lesson_id": str(lesson_a.id), "percent_complete": 50},
            format="json",
        )

        assert response.status_code == 403

    def test_progress_update_creates_entry(
        self, student_client, student, published_course, two_lessons
    ):
        Enrollment.objects.create(student=student, course=published_course)
        lesson_a, _ = two_lessons

        response = student_client.post(
            "/api/v1/progress/",
            {"lesson_id": str(lesson_a.id), "percent_complete": 50, "last_position_seconds": 30},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["percent_complete"] == 50

    def test_full_completion_issues_certificate_and_is_publicly_verifiable(
        self, student_client, student, published_course, two_lessons
    ):
        enrollment = Enrollment.objects.create(student=student, course=published_course)
        lesson_a, lesson_b = two_lessons

        r1 = student_client.post(
            "/api/v1/progress/",
            {"lesson_id": str(lesson_a.id), "percent_complete": 100},
            format="json",
        )
        assert r1.status_code == 200
        enrollment.refresh_from_db()
        assert enrollment.status == Enrollment.STATUS_ACTIVE  # only one of two lessons done

        r2 = student_client.post(
            "/api/v1/progress/",
            {"lesson_id": str(lesson_b.id), "percent_complete": 100},
            format="json",
        )
        assert r2.status_code == 200
        enrollment.refresh_from_db()
        assert enrollment.status == Enrollment.STATUS_COMPLETED

        cert_list = student_client.get("/api/v1/certificates/")
        assert len(cert_list.data["results"]) == 1
        certificate_uid = cert_list.data["results"][0]["certificate_uid"]

        # Verification is public — no auth.
        from rest_framework.test import APIClient

        anon = APIClient()
        verify = anon.get(f"/api/v1/certificates/{certificate_uid}/verify/")
        assert verify.status_code == 200
        assert verify.data["valid"] is True
        assert verify.data["course_title"] == published_course.title

    def test_verify_unknown_certificate_returns_404(self, api_client):
        response = api_client.get("/api/v1/certificates/does-not-exist/verify/")

        assert response.status_code == 404

    def test_progress_detail_is_owner_only(
        self, student_client, student, published_course, two_lessons, django_user_model
    ):
        enrollment = Enrollment.objects.create(student=student, course=published_course)

        other = django_user_model.objects.create_user(email="nosy@example.com", password="x")
        nosy_client = student_client.__class__()
        nosy_client.force_authenticate(user=other)

        response = nosy_client.get(f"/api/v1/progress/{enrollment.id}/")

        assert response.status_code == 403


class TestNotesAndBookmarks:
    def test_note_requires_enrollment(self, student_client, two_lessons):
        lesson_a, _ = two_lessons

        response = student_client.post(
            "/api/v1/lesson-notes/",
            {
                "lesson_id": str(lesson_a.id),
                "note_text": "Important point",
                "timestamp_seconds": 42,
            },
            format="json",
        )

        assert response.status_code == 403

    def test_note_created_when_enrolled(
        self, student_client, student, published_course, two_lessons
    ):
        Enrollment.objects.create(student=student, course=published_course)
        lesson_a, _ = two_lessons

        response = student_client.post(
            "/api/v1/lesson-notes/",
            {
                "lesson_id": str(lesson_a.id),
                "note_text": "Important point",
                "timestamp_seconds": 42,
            },
            format="json",
        )

        assert response.status_code == 201

    def test_bookmark_created_when_enrolled(
        self, student_client, student, published_course, two_lessons
    ):
        Enrollment.objects.create(student=student, course=published_course)
        lesson_a, _ = two_lessons

        response = student_client.post(
            "/api/v1/bookmarks/",
            {"lesson_id": str(lesson_a.id), "timestamp_seconds": 10, "label": "Key moment"},
            format="json",
        )

        assert response.status_code == 201


class TestWishlist:
    def test_add_and_list_and_remove(self, student_client, published_course):
        add = student_client.post(f"/api/v1/students/me/wishlist/{published_course.id}/")
        assert add.status_code == 201

        listing = student_client.get("/api/v1/students/me/wishlist/")
        assert len(listing.data) == 1
        assert listing.data[0]["course"]["id"] == str(published_course.id)

        remove = student_client.delete(f"/api/v1/students/me/wishlist/{published_course.id}/")
        assert remove.status_code == 204

        listing_after = student_client.get("/api/v1/students/me/wishlist/")
        assert listing_after.data == []

    def test_remove_when_not_wishlisted_returns_404(self, student_client, published_course):
        response = student_client.delete(f"/api/v1/students/me/wishlist/{published_course.id}/")

        assert response.status_code == 404

    def test_adding_twice_is_idempotent(self, student_client, published_course):
        first = student_client.post(f"/api/v1/students/me/wishlist/{published_course.id}/")
        second = student_client.post(f"/api/v1/students/me/wishlist/{published_course.id}/")

        assert first.status_code == 201
        assert second.status_code == 200
        listing = student_client.get("/api/v1/students/me/wishlist/")
        assert len(listing.data) == 1
