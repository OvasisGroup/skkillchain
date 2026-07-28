import pytest

from apps.assessments.models import CodingExercise, CodingExerciseSubmission
from apps.assessments.tasks import judge_coding_submission
from apps.catalog.models import Course
from apps.learning.models import Enrollment

pytestmark = pytest.mark.django_db


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
    c = Course.objects.create(owner=instructor, title="Coding Course")
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


@pytest.fixture
def enrolled_student(student, course):
    Enrollment.objects.create(student=student, course=course)
    return student


@pytest.fixture
def exercise(course):
    exercise = CodingExercise.objects.create(
        course=course,
        title="Double It",
        prompt="Read an integer n from stdin, print n * 2.",
        language=CodingExercise.LANGUAGE_PYTHON,
        time_limit_ms=2000,
        memory_limit_mb=128,
    )
    exercise.test_cases.create(input="3\n", expected_output="6", is_hidden=False, weight=1)
    exercise.test_cases.create(input="10\n", expected_output="20", is_hidden=True, weight=1)
    return exercise


class TestInstructorCodingExerciseCreate:
    def test_create_with_test_cases(self, instructor_client, course):
        response = instructor_client.post(
            f"/api/v1/instructor/courses/{course.id}/coding-exercises/",
            {
                "title": "Add Two Numbers",
                "prompt": "Print a + b.",
                "language": "python",
                "time_limit_ms": 2000,
                "memory_limit_mb": 128,
                "test_cases": [
                    {"input": "1 2\n", "expected_output": "3", "is_hidden": False, "weight": 1}
                ],
            },
            format="json",
        )

        assert response.status_code == 201
        exercise = CodingExercise.objects.get(id=response.data["id"])
        assert exercise.test_cases.count() == 1

    def test_requires_at_least_one_test_case(self, instructor_client, course):
        response = instructor_client.post(
            f"/api/v1/instructor/courses/{course.id}/coding-exercises/",
            {"title": "No Tests", "prompt": "x", "test_cases": []},
            format="json",
        )

        assert response.status_code == 400

    def test_non_owner_forbidden(self, student_client, course):
        response = student_client.post(
            f"/api/v1/instructor/courses/{course.id}/coding-exercises/",
            {"title": "Nope", "prompt": "x", "test_cases": [{"expected_output": "y"}]},
            format="json",
        )

        assert response.status_code == 403


class TestCodingExerciseDetail:
    def test_detail_requires_enrollment(self, student_client, exercise):
        response = student_client.get(f"/api/v1/coding-exercises/{exercise.id}/")

        assert response.status_code == 403

    def test_detail_never_exposes_test_cases(self, student_client, enrolled_student, exercise):
        response = student_client.get(f"/api/v1/coding-exercises/{exercise.id}/")

        assert response.status_code == 200
        assert "test_cases" not in response.data
        assert "expected_output" not in str(response.data)


class TestCodingExerciseSubmission:
    def test_submission_requires_enrollment(self, student_client, exercise):
        response = student_client.post(
            f"/api/v1/coding-exercises/{exercise.id}/submissions/",
            {"source_code": "print(int(input()) * 2)"},
            format="json",
        )

        assert response.status_code == 403

    def test_submission_queues_and_dispatches_grading(
        self, student_client, enrolled_student, exercise, monkeypatch
    ):
        dispatched = {}

        def fake_delay(submission_id):
            dispatched["id"] = submission_id

        monkeypatch.setattr("apps.assessments.views.judge_coding_submission.delay", fake_delay)

        response = student_client.post(
            f"/api/v1/coding-exercises/{exercise.id}/submissions/",
            {"source_code": "print(int(input()) * 2)"},
            format="json",
        )

        assert response.status_code == 202
        assert response.data["status"] == "queued"
        assert dispatched["id"] == response.data["id"]

    def test_submission_owner_only_can_view_result(
        self, student_client, enrolled_student, exercise, django_user_model
    ):
        submission = CodingExerciseSubmission.objects.create(
            coding_exercise=exercise,
            student=enrolled_student,
            language="python",
            source_code="print(1)",
        )
        stranger = django_user_model.objects.create_user(email="stranger@example.com", password="x")
        stranger_client = student_client.__class__()
        stranger_client.force_authenticate(user=stranger)

        response = stranger_client.get(
            f"/api/v1/coding-exercises/{exercise.id}/submissions/{submission.id}/"
        )

        assert response.status_code == 403

    def test_unsupported_language_rejected(self, student_client, enrolled_student, course):
        exercise = CodingExercise.objects.create(
            course=course, title="Ruby Exercise", prompt="x", language="python"
        )
        exercise.language = "ruby"
        exercise.save(update_fields=["language"])

        response = student_client.post(
            f"/api/v1/coding-exercises/{exercise.id}/submissions/",
            {"source_code": "puts 1"},
            format="json",
        )

        assert response.status_code == 400


class TestJudgeCodingSubmissionTask:
    """Runs the real Celery task function synchronously (not through the
    broker — that's covered by the live verification pass) against the
    real judge sandbox, exercising the full grade-and-persist path."""

    def test_correct_submission_is_graded_passed(self, enrolled_student, exercise):
        submission = CodingExerciseSubmission.objects.create(
            coding_exercise=exercise,
            student=enrolled_student,
            language="python",
            source_code="n = int(input())\nprint(n * 2)",
        )

        judge_coding_submission(str(submission.id))

        submission.refresh_from_db()
        assert submission.status == CodingExerciseSubmission.STATUS_PASSED
        assert submission.score == 100.0
        assert submission.graded_at is not None
        assert len(submission.result_detail) == 2
        # The hidden case's actual output must not appear in what's stored.
        hidden_result = next(r for r in submission.result_detail if r["is_hidden"])
        assert hidden_result["stdout"] is None

    def test_wrong_submission_is_graded_failed(self, enrolled_student, exercise):
        submission = CodingExerciseSubmission.objects.create(
            coding_exercise=exercise,
            student=enrolled_student,
            language="python",
            source_code="n = int(input())\nprint(n + 1)",  # wrong operation
        )

        judge_coding_submission(str(submission.id))

        submission.refresh_from_db()
        assert submission.status == CodingExerciseSubmission.STATUS_FAILED
        assert submission.score == 0.0

    def test_no_test_cases_results_in_error_status(self, enrolled_student, course):
        exercise = CodingExercise.objects.create(course=course, title="Empty", prompt="x")
        submission = CodingExerciseSubmission.objects.create(
            coding_exercise=exercise,
            student=enrolled_student,
            language="python",
            source_code="pass",
        )

        judge_coding_submission(str(submission.id))

        submission.refresh_from_db()
        assert submission.status == CodingExerciseSubmission.STATUS_ERROR
