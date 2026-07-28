import pytest

from apps.assessments.models import Answer, Question, Quiz, QuizAttempt
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
    c = Course.objects.create(owner=instructor, title="Quiz Course")
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


@pytest.fixture
def enrolled_student(student, course):
    Enrollment.objects.create(student=student, course=course)
    return student


@pytest.fixture
def quiz(course):
    quiz = Quiz.objects.create(course=course, title="Basics", attempts_allowed=1, pass_score=70)
    q1 = Question.objects.create(quiz=quiz, type=Question.TYPE_SINGLE_CHOICE, prompt="2+2?")
    Answer.objects.create(question=q1, text="4", is_correct=True)
    Answer.objects.create(question=q1, text="5", is_correct=False)

    q2 = Question.objects.create(quiz=quiz, type=Question.TYPE_MULTIPLE_CHOICE, prompt="Primes?")
    Answer.objects.create(question=q2, text="2", is_correct=True)
    Answer.objects.create(question=q2, text="3", is_correct=True)
    Answer.objects.create(question=q2, text="4", is_correct=False)
    return quiz


def _correct_answer_ids(question):
    return list(question.answers.filter(is_correct=True).values_list("id", flat=True))


class TestInstructorQuizCreate:
    def test_create_quiz_with_nested_questions_and_answers(self, instructor_client, course):
        response = instructor_client.post(
            f"/api/v1/instructor/courses/{course.id}/quizzes/",
            {
                "title": "New Quiz",
                "attempts_allowed": 2,
                "pass_score": 60,
                "questions": [
                    {
                        "type": "single_choice",
                        "prompt": "Capital of France?",
                        "answers": [
                            {"text": "Paris", "is_correct": True},
                            {"text": "Lyon", "is_correct": False},
                        ],
                    }
                ],
            },
            format="json",
        )

        assert response.status_code == 201
        created = Quiz.objects.get(id=response.data["id"])
        assert created.questions.count() == 1
        assert created.questions.first().answers.count() == 2
        assert created.questions.first().answers.filter(is_correct=True).count() == 1

    def test_question_without_correct_answer_rejected(self, instructor_client, course):
        response = instructor_client.post(
            f"/api/v1/instructor/courses/{course.id}/quizzes/",
            {
                "title": "Bad Quiz",
                "questions": [
                    {
                        "prompt": "No right answer?",
                        "answers": [{"text": "A", "is_correct": False}],
                    }
                ],
            },
            format="json",
        )

        assert response.status_code == 400

    def test_non_owner_cannot_create_quiz(self, student_client, course):
        response = student_client.post(
            f"/api/v1/instructor/courses/{course.id}/quizzes/", {"title": "Nope"}, format="json"
        )

        assert response.status_code == 403

    def test_section_must_belong_to_the_same_course(self, instructor_client, instructor, course):
        from apps.catalog.models import Course
        from apps.content.models import Section

        other_course = Course.objects.create(owner=instructor, title="Other Course")
        other_section = Section.objects.create(course=other_course, title="Foreign Section")

        response = instructor_client.post(
            f"/api/v1/instructor/courses/{course.id}/quizzes/",
            {"title": "Cross-linked Quiz", "section": str(other_section.id)},
            format="json",
        )

        assert response.status_code == 400


class TestQuizDetail:
    def test_detail_hides_is_correct(self, student_client, enrolled_student, quiz):
        response = student_client.get(f"/api/v1/quizzes/{quiz.id}/")

        assert response.status_code == 200
        body = str(response.data)
        assert "is_correct" not in body

    def test_detail_requires_enrollment(self, student_client, quiz):
        response = student_client.get(f"/api/v1/quizzes/{quiz.id}/")

        assert response.status_code == 403


class TestQuizAttemptFlow:
    def test_start_attempt_requires_enrollment(self, student_client, quiz):
        response = student_client.post(f"/api/v1/quizzes/{quiz.id}/attempts/")

        assert response.status_code == 403

    def test_cannot_start_second_attempt_while_one_in_progress(
        self, student_client, enrolled_student, quiz
    ):
        first = student_client.post(f"/api/v1/quizzes/{quiz.id}/attempts/")
        assert first.status_code == 201

        second = student_client.post(f"/api/v1/quizzes/{quiz.id}/attempts/")
        assert second.status_code == 400

    def test_submit_without_attempt_rejected(self, student_client, enrolled_student, quiz):
        response = student_client.post(
            f"/api/v1/quizzes/{quiz.id}/submit/", {"responses": []}, format="json"
        )

        assert response.status_code == 400

    def test_fully_correct_submission_passes(self, student_client, enrolled_student, quiz):
        student_client.post(f"/api/v1/quizzes/{quiz.id}/attempts/")
        q1, q2 = quiz.questions.all()

        response = student_client.post(
            f"/api/v1/quizzes/{quiz.id}/submit/",
            {
                "responses": [
                    {
                        "question_id": str(q1.id),
                        "answer_ids": [str(i) for i in _correct_answer_ids(q1)],
                    },
                    {
                        "question_id": str(q2.id),
                        "answer_ids": [str(i) for i in _correct_answer_ids(q2)],
                    },
                ]
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["score"] == 100.0
        assert response.data["passed"] is True

    def test_partial_multiple_choice_selection_counts_as_incorrect(
        self, student_client, enrolled_student, quiz
    ):
        student_client.post(f"/api/v1/quizzes/{quiz.id}/attempts/")
        q1, q2 = quiz.questions.all()
        correct_q2_ids = _correct_answer_ids(q2)

        response = student_client.post(
            f"/api/v1/quizzes/{quiz.id}/submit/",
            {
                "responses": [
                    {
                        "question_id": str(q1.id),
                        "answer_ids": [str(i) for i in _correct_answer_ids(q1)],
                    },
                    # Only one of the two correct answers selected — must
                    # not count as correct for a multiple_choice question.
                    {"question_id": str(q2.id), "answer_ids": [str(correct_q2_ids[0])]},
                ]
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["score"] == 50.0
        assert response.data["passed"] is False  # pass_score is 70

    def test_wrong_answer_fails_and_is_below_pass_score(
        self, student_client, enrolled_student, quiz
    ):
        student_client.post(f"/api/v1/quizzes/{quiz.id}/attempts/")
        q1, q2 = quiz.questions.all()
        wrong_q1_id = q1.answers.filter(is_correct=False).first().id

        response = student_client.post(
            f"/api/v1/quizzes/{quiz.id}/submit/",
            {
                "responses": [
                    {"question_id": str(q1.id), "answer_ids": [str(wrong_q1_id)]},
                    {
                        "question_id": str(q2.id),
                        "answer_ids": [str(i) for i in _correct_answer_ids(q2)],
                    },
                ]
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["score"] == 50.0
        assert response.data["passed"] is False

    def test_attempts_allowed_enforced(self, student_client, enrolled_student, quiz):
        # quiz fixture has attempts_allowed=1
        student_client.post(f"/api/v1/quizzes/{quiz.id}/attempts/")
        q1, q2 = quiz.questions.all()
        student_client.post(
            f"/api/v1/quizzes/{quiz.id}/submit/",
            {
                "responses": [
                    {
                        "question_id": str(q1.id),
                        "answer_ids": [str(i) for i in _correct_answer_ids(q1)],
                    },
                    {
                        "question_id": str(q2.id),
                        "answer_ids": [str(i) for i in _correct_answer_ids(q2)],
                    },
                ]
            },
            format="json",
        )

        second_attempt = student_client.post(f"/api/v1/quizzes/{quiz.id}/attempts/")

        assert second_attempt.status_code == 400
        assert QuizAttempt.objects.filter(quiz=quiz, student=enrolled_student).count() == 1
