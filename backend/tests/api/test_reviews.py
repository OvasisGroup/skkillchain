from decimal import Decimal

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.models import Course
from apps.learning.models import Enrollment
from apps.reviews.models import CourseDiscussionPost, Review
from config.asgi import application

pytestmark = pytest.mark.django_db


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


@pytest.fixture
def student(django_user_model):
    return django_user_model.objects.create_user(email="student@example.com", password="x")


@pytest.fixture
def other_student(django_user_model):
    return django_user_model.objects.create_user(email="other@example.com", password="x")


@pytest.fixture
def student_client(api_client, student):
    api_client.force_authenticate(user=student)
    return api_client


@pytest.fixture
def course(instructor):
    c = Course.objects.create(
        owner=instructor, title="Review Course", price_amount=Decimal("50.00")
    )
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


@pytest.fixture
def completed_enrollment(student, course):
    return Enrollment.objects.create(
        student=student, course=course, status=Enrollment.STATUS_COMPLETED
    )


@pytest.fixture
def active_enrollment(student, course):
    return Enrollment.objects.create(
        student=student, course=course, status=Enrollment.STATUS_ACTIVE
    )


class TestReviewCreate:
    def test_requires_completed_enrollment(self, student_client, course):
        response = student_client.post(
            f"/api/v1/courses/{course.id}/reviews/", {"rating": 5}, format="json"
        )

        assert response.status_code == 403
        assert not Review.objects.filter(course=course).exists()

    def test_active_but_not_completed_enrollment_is_rejected(
        self, student_client, course, active_enrollment
    ):
        response = student_client.post(
            f"/api/v1/courses/{course.id}/reviews/", {"rating": 5}, format="json"
        )

        assert response.status_code == 403

    def test_completed_enrollment_can_review(self, student_client, course, completed_enrollment):
        response = student_client.post(
            f"/api/v1/courses/{course.id}/reviews/",
            {"rating": 4, "review_text": "Great course"},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["is_verified_purchase"] is True
        assert response.data["rating"] == 4

    def test_cannot_review_same_course_twice(self, student_client, course, completed_enrollment):
        student_client.post(f"/api/v1/courses/{course.id}/reviews/", {"rating": 4}, format="json")

        response = student_client.post(
            f"/api/v1/courses/{course.id}/reviews/", {"rating": 2}, format="json"
        )

        assert response.status_code == 400

    def test_reviews_are_publicly_readable(self, api_client, course, student, completed_enrollment):
        Review.objects.create(course=course, user=student, rating=5, is_verified_purchase=True)

        response = api_client.get(f"/api/v1/courses/{course.id}/reviews/")

        assert response.status_code == 200
        assert len(response.data["results"]) == 1


class TestReviewUpdateDestroy:
    def test_owner_can_update(self, student_client, course, student):
        review = Review.objects.create(
            course=course, user=student, rating=3, is_verified_purchase=True
        )

        response = student_client.patch(
            f"/api/v1/reviews/{review.id}/", {"rating": 5}, format="json"
        )

        assert response.status_code == 200
        review.refresh_from_db()
        assert review.rating == 5

    def test_non_owner_cannot_update(self, student_client, course, other_student):
        review = Review.objects.create(
            course=course, user=other_student, rating=3, is_verified_purchase=True
        )

        response = student_client.patch(
            f"/api/v1/reviews/{review.id}/", {"rating": 1}, format="json"
        )

        assert response.status_code == 403

    def test_owner_can_delete(self, student_client, course, student):
        review = Review.objects.create(
            course=course, user=student, rating=3, is_verified_purchase=True
        )

        response = student_client.delete(f"/api/v1/reviews/{review.id}/")

        assert response.status_code == 204
        assert not Review.objects.filter(id=review.id).exists()


class TestCourseDiscussions:
    def test_requires_enrollment_any_status(self, student_client, course):
        response = student_client.post(
            f"/api/v1/courses/{course.id}/discussions/", {"body": "hi"}, format="json"
        )

        assert response.status_code == 403

    def test_active_enrollment_can_post(self, student_client, student, course, active_enrollment):
        response = student_client.post(
            f"/api/v1/courses/{course.id}/discussions/",
            {"body": "question about lesson 2"},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["user_email"] == student.email
        assert CourseDiscussionPost.objects.filter(
            course=course, body="question about lesson 2"
        ).exists()

    def test_list_includes_poster_email(self, api_client, student_client, student, course, active_enrollment):
        student_client.post(
            f"/api/v1/courses/{course.id}/discussions/", {"body": "hi everyone"}, format="json"
        )

        response = api_client.get(f"/api/v1/courses/{course.id}/discussions/")

        assert response.status_code == 200
        assert response.data["results"][0]["user_email"] == student.email


class TestDiscussionWebsocket:
    @database_sync_to_async
    def _access_token(self, user) -> str:
        return str(RefreshToken.for_user(user).access_token)

    @pytest.mark.django_db(transaction=True)
    async def test_enrolled_students_receive_live_posts(self, student, other_student, course):
        from apps.learning.models import Enrollment as EnrollmentModel

        await database_sync_to_async(EnrollmentModel.objects.create)(
            student=student, course=course, status=EnrollmentModel.STATUS_ACTIVE
        )
        await database_sync_to_async(EnrollmentModel.objects.create)(
            student=other_student, course=course, status=EnrollmentModel.STATUS_ACTIVE
        )
        path = f"/ws/course/{course.id}/discussion/"

        poster_token = await self._access_token(student)
        watcher_token = await self._access_token(other_student)
        poster_ws = WebsocketCommunicator(application, f"{path}?token={poster_token}")
        watcher_ws = WebsocketCommunicator(application, f"{path}?token={watcher_token}")
        try:
            assert (await poster_ws.connect())[0]
            assert (await watcher_ws.connect())[0]

            await poster_ws.send_json_to({"body": "hello class"})

            delivered = await watcher_ws.receive_json_from(timeout=5)
            assert delivered["body"] == "hello class"
        finally:
            await poster_ws.disconnect()
            await watcher_ws.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_non_enrolled_user_cannot_join(self, other_student, course):
        token = await self._access_token(other_student)
        ws = WebsocketCommunicator(application, f"/ws/course/{course.id}/discussion/?token={token}")

        connected, _ = await ws.connect()

        assert connected is False
        await ws.disconnect()
