import pytest
from rest_framework.test import APIClient

from apps.assessments.models import Assignment, AssignmentSubmission
from apps.catalog.models import Course
from apps.learning.models import Enrollment

pytestmark = pytest.mark.django_db


def _client_for(user):
    # api_client/instructor_client/student_client all wrap the *same*
    # underlying test client per test (pytest fixture caching), so a test
    # needing two independently authenticated users at once must build a
    # second APIClient explicitly rather than combining two named fixtures.
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


@pytest.fixture
def instructor_client(api_client, instructor):
    api_client.force_authenticate(user=instructor)
    return api_client


@pytest.fixture
def student(django_user_model):
    return django_user_model.objects.create_user(email="student@example.com", password="x")


@pytest.fixture
def student_client(api_client, student):
    api_client.force_authenticate(user=student)
    return api_client


@pytest.fixture
def course(instructor):
    c = Course.objects.create(owner=instructor, title="Assignment Course")
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


@pytest.fixture
def enrolled_student(student, course):
    Enrollment.objects.create(student=student, course=course)
    return student


@pytest.fixture
def assignment(course):
    return Assignment.objects.create(
        course=course, title="Essay", instructions="Write 500 words.", due_policy={"due_at": None}
    )


class TestInstructorAssignmentCreate:
    def test_create(self, instructor_client, course):
        response = instructor_client.post(
            f"/api/v1/instructor/courses/{course.id}/assignments/",
            {"title": "Project", "instructions": "Build something.", "due_policy": {}},
            format="json",
        )

        assert response.status_code == 201
        assert Assignment.objects.filter(course=course, title="Project").exists()

    def test_non_owner_forbidden(self, student_client, course):
        response = student_client.post(
            f"/api/v1/instructor/courses/{course.id}/assignments/",
            {"title": "Nope", "instructions": "x"},
            format="json",
        )

        assert response.status_code == 403


class TestAssignmentSubmission:
    def test_submit_requires_enrollment(self, student_client, assignment):
        response = student_client.post(
            f"/api/v1/assignments/{assignment.id}/submissions/",
            {"content_ref": "https://example.com/my-essay"},
            format="json",
        )

        assert response.status_code == 403

    def test_submit_creates_row(self, student_client, enrolled_student, assignment):
        response = student_client.post(
            f"/api/v1/assignments/{assignment.id}/submissions/",
            {"content_ref": "https://example.com/my-essay"},
            format="json",
        )

        assert response.status_code == 201
        assert AssignmentSubmission.objects.filter(
            assignment=assignment, student=enrolled_student
        ).exists()

    def test_resubmit_before_grading_updates_existing_row(
        self, student_client, enrolled_student, assignment
    ):
        student_client.post(
            f"/api/v1/assignments/{assignment.id}/submissions/",
            {"content_ref": "https://example.com/draft-1"},
            format="json",
        )

        response = student_client.post(
            f"/api/v1/assignments/{assignment.id}/submissions/",
            {"content_ref": "https://example.com/draft-2"},
            format="json",
        )

        assert response.status_code == 200
        assert AssignmentSubmission.objects.filter(assignment=assignment).count() == 1
        submission = AssignmentSubmission.objects.get(
            assignment=assignment, student=enrolled_student
        )
        assert submission.content_ref == "https://example.com/draft-2"

    def test_resubmit_after_grading_rejected(
        self, student_client, enrolled_student, assignment, instructor
    ):
        submit = student_client.post(
            f"/api/v1/assignments/{assignment.id}/submissions/",
            {"content_ref": "https://example.com/final"},
            format="json",
        )
        submission_id = submit.data["id"]
        _client_for(instructor).post(
            f"/api/v1/instructor/assignments/{assignment.id}/submissions/{submission_id}/grade/",
            {"grade": 90, "feedback": "Great work."},
            format="json",
        )

        response = student_client.post(
            f"/api/v1/assignments/{assignment.id}/submissions/",
            {"content_ref": "https://example.com/resubmit-attempt"},
            format="json",
        )

        assert response.status_code == 400


class TestInstructorGrading:
    def test_grade_submission(self, student_client, enrolled_student, assignment, instructor):
        submit = student_client.post(
            f"/api/v1/assignments/{assignment.id}/submissions/",
            {"content_ref": "https://example.com/final"},
            format="json",
        )
        submission_id = submit.data["id"]

        response = _client_for(instructor).post(
            f"/api/v1/instructor/assignments/{assignment.id}/submissions/{submission_id}/grade/",
            {"grade": 85, "feedback": "Solid."},
            format="json",
        )

        assert response.status_code == 200
        submission = AssignmentSubmission.objects.get(id=submission_id)
        assert submission.grade == 85
        assert submission.graded_by == instructor
        assert submission.graded_at is not None

    def test_non_owner_cannot_grade(
        self, student_client, enrolled_student, assignment, django_user_model
    ):
        submit = student_client.post(
            f"/api/v1/assignments/{assignment.id}/submissions/",
            {"content_ref": "https://example.com/final"},
            format="json",
        )
        submission_id = submit.data["id"]
        other_instructor = django_user_model.objects.create_user(
            email="other@example.com", password="x"
        )

        response = _client_for(other_instructor).post(
            f"/api/v1/instructor/assignments/{assignment.id}/submissions/{submission_id}/grade/",
            {"grade": 50},
            format="json",
        )

        assert response.status_code == 403

    def test_non_owner_cannot_list_submissions(self, student_client, assignment):
        response = student_client.get(
            f"/api/v1/instructor/assignments/{assignment.id}/submissions/"
        )

        assert response.status_code == 403

    def test_owner_lists_submissions(
        self, student_client, enrolled_student, assignment, instructor
    ):
        student_client.post(
            f"/api/v1/assignments/{assignment.id}/submissions/",
            {"content_ref": "https://example.com/final"},
            format="json",
        )

        response = _client_for(instructor).get(
            f"/api/v1/instructor/assignments/{assignment.id}/submissions/"
        )

        assert response.status_code == 200
        assert len(response.data) == 1


class TestMyGrades:
    def test_lists_graded_assignment(
        self, student_client, enrolled_student, assignment, instructor
    ):
        submit = student_client.post(
            f"/api/v1/assignments/{assignment.id}/submissions/",
            {"content_ref": "https://example.com/final"},
            format="json",
        )
        _client_for(instructor).post(
            f"/api/v1/instructor/assignments/{assignment.id}/submissions/{submit.data['id']}/grade/",
            {"grade": 77},
            format="json",
        )

        response = student_client.get("/api/v1/students/me/grades/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["type"] == "assignment"
        assert response.data[0]["grade"] == 77

    def test_ungraded_submission_excluded(self, student_client, enrolled_student, assignment):
        student_client.post(
            f"/api/v1/assignments/{assignment.id}/submissions/",
            {"content_ref": "https://example.com/final"},
            format="json",
        )

        response = student_client.get("/api/v1/students/me/grades/")

        assert response.data == []
