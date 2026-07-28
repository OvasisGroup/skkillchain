from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.catalog.models import Course
from apps.learning.models import Enrollment

from .models import (
    Assignment,
    AssignmentSubmission,
    CodingExercise,
    CodingExerciseSubmission,
    Question,
    Quiz,
    QuizAttempt,
    QuizResponse,
)
from .serializers import (
    AssignmentCreateSerializer,
    AssignmentGradeSerializer,
    AssignmentSerializer,
    AssignmentSubmissionCreateSerializer,
    AssignmentSubmissionSerializer,
    CodingExerciseCreateSerializer,
    CodingExerciseDetailSerializer,
    CodingExerciseSubmissionCreateSerializer,
    CodingExerciseSubmissionSerializer,
    GradeEntrySerializer,
    QuizAttemptSerializer,
    QuizCreateSerializer,
    QuizDetailSerializer,
    QuizSubmitSerializer,
)
from .tasks import judge_coding_submission


def _owned_course_or_403(course_id, user):
    course = get_object_or_404(Course, pk=course_id)
    if course.owner_id != user.id:
        raise PermissionDenied("You do not own this course.")
    return course


def _require_enrollment(user, course_id):
    if not Enrollment.objects.filter(student=user, course_id=course_id).exists():
        raise PermissionDenied("You must be enrolled in this course.")


# ---------- Instructor authoring ----------


_QUIZ_CREATE_EXAMPLE = {
    "title": "Basics Quiz",
    "attempts_allowed": 2,
    "pass_score": 70,
    "questions": [
        {
            "type": "single_choice",
            "prompt": "2 + 2?",
            "answers": [
                {"text": "4", "is_correct": True},
                {"text": "5", "is_correct": False},
            ],
        }
    ],
}


@extend_schema(
    tags=["Instructor"],
    request=QuizCreateSerializer,
    responses={201: QuizDetailSerializer},
    description="Creates a quiz (optionally with nested questions/answers in one call) for a "
    "course the current instructor owns. Every question needs at least one answer marked "
    "is_correct. If section is given, it must belong to the same course.",
    examples=[
        OpenApiExample("Create quiz", value=_QUIZ_CREATE_EXAMPLE, request_only=True),
        OpenApiExample(
            "Created",
            value={
                "id": "b1c2d3e4-...",
                "title": "Basics Quiz",
                "attempts_allowed": 2,
                "pass_score": 70,
                "questions": [
                    {
                        "id": "c1d2e3f4-...",
                        "type": "single_choice",
                        "prompt": "2 + 2?",
                        "sort_order": 0,
                        "answers": [
                            {"id": "d1e2f3a4-...", "text": "4", "sort_order": 0},
                            {"id": "e1f2a3b4-...", "text": "5", "sort_order": 0},
                        ],
                    }
                ],
            },
            response_only=True,
        ),
    ],
)
class InstructorQuizCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id):
        course = _owned_course_or_403(course_id, request.user)
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        section = serializer.validated_data.get("section")
        if section is not None and section.course_id != course.id:
            raise ValidationError("section must belong to the same course as this quiz.")
        quiz = serializer.save(course=course)
        record_event(
            actor=request.user,
            action="quiz.create",
            entity_type="Quiz",
            entity_id=quiz.id,
            request=request,
        )
        return Response(QuizDetailSerializer(quiz).data, status=201)


@extend_schema(
    tags=["Instructor"],
    request=AssignmentCreateSerializer,
    responses={201: AssignmentSerializer},
    description="Creates a written/file assignment for a course the current instructor owns.",
    examples=[
        OpenApiExample(
            "Create assignment",
            value={
                "title": "Final Project",
                "instructions": "Submit a link to your GitHub repo.",
                "due_policy": "7 days after enrollment",
            },
            request_only=True,
        ),
        OpenApiExample(
            "Created",
            value={
                "id": "a1b2c3d4-...",
                "course": "1c2d3e4f-...",
                "title": "Final Project",
                "instructions": "Submit a link to your GitHub repo.",
                "due_policy": "7 days after enrollment",
            },
            response_only=True,
        ),
    ],
)
class InstructorAssignmentCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id):
        course = _owned_course_or_403(course_id, request.user)
        serializer = AssignmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save(course=course)
        record_event(
            actor=request.user,
            action="assignment.create",
            entity_type="Assignment",
            entity_id=assignment.id,
            request=request,
        )
        return Response(AssignmentSerializer(assignment).data, status=201)


@extend_schema(
    tags=["Instructor"],
    request=CodingExerciseCreateSerializer,
    responses={201: CodingExerciseDetailSerializer},
    description="Creates a judged coding exercise (with hidden/visible test cases) for a "
    "course the current instructor owns. Requires at least one test case.",
    examples=[
        OpenApiExample(
            "Create exercise",
            value={
                "title": "Reverse a string",
                "prompt": "Write a function reverse(s) that returns s reversed.",
                "starter_code": "def reverse(s):\n    ...\n",
                "language": "python",
                "time_limit_ms": 2000,
                "memory_limit_mb": 128,
                "test_cases": [
                    {"input": "hello", "expected_output": "olleh", "is_hidden": False, "weight": 1}
                ],
            },
            request_only=True,
        ),
        OpenApiExample(
            "Created",
            value={
                "id": "b2c3d4e5-...",
                "title": "Reverse a string",
                "prompt": "Write a function reverse(s) that returns s reversed.",
                "starter_code": "def reverse(s):\n    ...\n",
                "language": "python",
                "time_limit_ms": 2000,
                "memory_limit_mb": 128,
            },
            response_only=True,
        ),
    ],
)
class InstructorCodingExerciseCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id):
        course = _owned_course_or_403(course_id, request.user)
        serializer = CodingExerciseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exercise = serializer.save(course=course)
        record_event(
            actor=request.user,
            action="coding_exercise.create",
            entity_type="CodingExercise",
            entity_id=exercise.id,
            request=request,
        )
        return Response(CodingExerciseDetailSerializer(exercise).data, status=201)


_ASSIGNMENT_SUBMISSION_EXAMPLE = {
    "id": "c3d4e5f6-...",
    "assignment": "a1b2c3d4-...",
    "student_email": "student@example.com",
    "content_ref": "https://github.com/student/final-project",
    "grade": None,
    "feedback": "",
    "graded_at": None,
    "submitted_at": "2026-01-30T12:00:00Z",
    "ai_suggested_grade": None,
    "ai_suggested_feedback": "",
    "ai_suggested_at": None,
}


@extend_schema(
    tags=["Instructor"],
    description="Lists submissions for an assignment the current instructor owns.",
    examples=[
        OpenApiExample("Submission", value=_ASSIGNMENT_SUBMISSION_EXAMPLE, response_only=True)
    ],
)
class InstructorAssignmentSubmissionsListView(generics.ListAPIView):
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        assignment = get_object_or_404(Assignment, pk=self.kwargs["id"])
        _owned_course_or_403(assignment.course_id, self.request.user)
        return assignment.submissions.select_related("student")


@extend_schema(
    tags=["Instructor"],
    request=AssignmentGradeSerializer,
    responses={200: AssignmentSubmissionSerializer},
    description="Grades an assignment submission for an assignment the current instructor "
    "owns — overwrites any prior grade (manual or AI-approved).",
    examples=[
        OpenApiExample(
            "Grade", value={"grade": 92, "feedback": "Great work overall."}, request_only=True
        ),
        OpenApiExample(
            "Graded",
            value={
                **_ASSIGNMENT_SUBMISSION_EXAMPLE,
                "grade": 92,
                "feedback": "Great work overall.",
                "graded_at": "2026-02-01T09:00:00Z",
            },
            response_only=True,
        ),
    ],
)
class InstructorAssignmentGradeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id, submission_id):
        submission = get_object_or_404(AssignmentSubmission, pk=submission_id, assignment_id=id)
        _owned_course_or_403(submission.assignment.course_id, request.user)

        serializer = AssignmentGradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission.grade = serializer.validated_data["grade"]
        submission.feedback = serializer.validated_data.get("feedback", "")
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.save(update_fields=["grade", "feedback", "graded_by", "graded_at"])
        record_event(
            actor=request.user,
            action="assignment_submission.grade",
            entity_type="AssignmentSubmission",
            entity_id=submission.id,
            request=request,
        )
        return Response(AssignmentSubmissionSerializer(submission).data)


@extend_schema(
    tags=["Instructor"],
    request=None,
    responses={200: AssignmentSubmissionSerializer},
    description="Approves an AI-suggested grade as-is, copying ai_suggested_grade/"
    "ai_suggested_feedback into grade/feedback. Fails with 400 if no AI suggestion exists yet "
    "— to edit the AI's suggestion instead of approving it verbatim, use "
    "POST .../submissions/{id}/grade/ with the desired values.",
    examples=[
        OpenApiExample(
            "Approved",
            value={
                **_ASSIGNMENT_SUBMISSION_EXAMPLE,
                "grade": 88,
                "feedback": "Solid implementation, minor style nits.",
                "graded_at": "2026-02-01T09:00:00Z",
                "ai_suggested_grade": 88,
                "ai_suggested_feedback": "Solid implementation, minor style nits.",
                "ai_suggested_at": "2026-01-31T09:00:00Z",
            },
            response_only=True,
        )
    ],
)
class AssignmentSubmissionApproveAIGradeView(APIView):
    """The instructor's explicit approval action — an AI-suggested grade
    can reach `grade`/`graded_by`/`graded_at` only through this endpoint,
    never automatically. See apps.ai.services.suggest_assignment_grade,
    which only ever writes ai_suggested_*."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, submission_id):
        submission = get_object_or_404(AssignmentSubmission, pk=submission_id)
        _owned_course_or_403(submission.assignment.course_id, request.user)

        if submission.ai_suggested_at is None:
            raise ValidationError("No AI grade suggestion exists for this submission yet.")

        submission.grade = submission.ai_suggested_grade
        submission.feedback = submission.ai_suggested_feedback
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.save(update_fields=["grade", "feedback", "graded_by", "graded_at"])
        record_event(
            actor=request.user,
            action="assignment_submission.approve_ai_grade",
            entity_type="AssignmentSubmission",
            entity_id=submission.id,
            request=request,
        )
        return Response(AssignmentSubmissionSerializer(submission).data)


# ---------- Quizzes (student) ----------


@extend_schema(
    tags=["Student"],
    responses={200: QuizDetailSerializer},
    description="Gets a quiz's questions/answers for an enrolled student — is_correct is "
    "never included here, so a student can't inspect the answer key before attempting.",
    examples=[
        OpenApiExample(
            "Quiz",
            value={
                "id": "b1c2d3e4-...",
                "title": "Basics Quiz",
                "attempts_allowed": 2,
                "pass_score": 70,
                "questions": [
                    {
                        "id": "c1d2e3f4-...",
                        "type": "single_choice",
                        "prompt": "2 + 2?",
                        "sort_order": 0,
                        "answers": [
                            {"id": "d1e2f3a4-...", "text": "4", "sort_order": 0},
                            {"id": "e1f2a3b4-...", "text": "5", "sort_order": 0},
                        ],
                    }
                ],
            },
            response_only=True,
        )
    ],
)
class QuizDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        quiz = get_object_or_404(Quiz, pk=id)
        _require_enrollment(request.user, quiz.course_id)
        return Response(QuizDetailSerializer(quiz).data)


@extend_schema(
    tags=["Student"],
    request=None,
    responses={201: QuizAttemptSerializer},
    description="Starts a quiz attempt for an enrolled student. Fails with 400 if an attempt "
    "is already in progress, or attempts_allowed has been used up.",
    examples=[
        OpenApiExample(
            "Attempt started",
            value={
                "id": "f1e2d3c4-...",
                "quiz": "b1c2d3e4-...",
                "status": "in_progress",
                "started_at": "2026-02-01T10:00:00Z",
                "submitted_at": None,
                "score": None,
                "passed": None,
            },
            response_only=True,
        )
    ],
)
class QuizAttemptStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        quiz = get_object_or_404(Quiz, pk=id)
        _require_enrollment(request.user, quiz.course_id)

        if QuizAttempt.objects.filter(
            quiz=quiz, student=request.user, status=QuizAttempt.STATUS_IN_PROGRESS
        ).exists():
            raise ValidationError("You already have an attempt in progress on this quiz.")

        finished_count = QuizAttempt.objects.filter(
            quiz=quiz, student=request.user, status=QuizAttempt.STATUS_SUBMITTED
        ).count()
        if finished_count >= quiz.attempts_allowed:
            raise ValidationError("No attempts remaining for this quiz.")

        attempt = QuizAttempt.objects.create(quiz=quiz, student=request.user)
        record_event(
            actor=request.user,
            action="quiz_attempt.start",
            entity_type="QuizAttempt",
            entity_id=attempt.id,
            request=request,
        )
        return Response(QuizAttemptSerializer(attempt).data, status=201)


@extend_schema(
    tags=["Student"],
    request=QuizSubmitSerializer,
    responses={200: QuizAttemptSerializer},
    description="Submits answers for the in-progress attempt, grades it immediately (a "
    "multiple_choice question only counts as correct if every correct answer, and no "
    "incorrect one, was selected), and marks the attempt passed/failed against pass_score.",
    examples=[
        OpenApiExample(
            "Submit",
            value={"responses": [{"question_id": "c1d2e3f4-...", "answer_ids": ["d1e2f3a4-..."]}]},
            request_only=True,
        ),
        OpenApiExample(
            "Graded",
            value={
                "id": "f1e2d3c4-...",
                "quiz": "b1c2d3e4-...",
                "status": "submitted",
                "started_at": "2026-02-01T10:00:00Z",
                "submitted_at": "2026-02-01T10:05:00Z",
                "score": 100.0,
                "passed": True,
            },
            response_only=True,
        ),
    ],
)
class QuizSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        quiz = get_object_or_404(Quiz, pk=id)
        _require_enrollment(request.user, quiz.course_id)

        attempt = QuizAttempt.objects.filter(
            quiz=quiz, student=request.user, status=QuizAttempt.STATUS_IN_PROGRESS
        ).first()
        if attempt is None:
            raise ValidationError("No attempt in progress — start one first.")

        serializer = QuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        responses_data = serializer.validated_data["responses"]

        questions = {q.id: q for q in quiz.questions.prefetch_related("answers")}
        correct_count = 0

        for response_data in responses_data:
            question: Question | None = questions.get(response_data["question_id"])
            if question is None:
                raise ValidationError(
                    f"Question {response_data['question_id']} does not belong to this quiz."
                )
            answers_by_id = {a.id: a for a in question.answers.all()}
            correct_ids = {aid for aid, a in answers_by_id.items() if a.is_correct}
            selected_ids = set(response_data["answer_ids"])
            is_correct = selected_ids == correct_ids
            if is_correct:
                correct_count += 1

            quiz_response = QuizResponse.objects.create(
                attempt=attempt, question=question, is_correct=is_correct
            )
            quiz_response.selected_answers.set(
                [aid for aid in selected_ids if aid in answers_by_id]
            )

        total_questions = len(questions)
        score = (correct_count / total_questions * 100) if total_questions else 0.0
        attempt.status = QuizAttempt.STATUS_SUBMITTED
        attempt.submitted_at = timezone.now()
        attempt.score = score
        attempt.passed = score >= quiz.pass_score
        attempt.save(update_fields=["status", "submitted_at", "score", "passed"])

        record_event(
            actor=request.user,
            action="quiz_attempt.submit",
            entity_type="QuizAttempt",
            entity_id=attempt.id,
            request=request,
            payload={"score": score, "passed": attempt.passed},
        )
        return Response(QuizAttemptSerializer(attempt).data)


# ---------- Assignments (student) ----------


@extend_schema(
    tags=["Student"],
    request=AssignmentSubmissionCreateSerializer,
    responses={201: AssignmentSubmissionSerializer, 200: AssignmentSubmissionSerializer},
    description="Submits (or resubmits, before grading) an assignment for an enrolled "
    "student. Returns 200 (not 201) when replacing an ungraded submission; fails with 400 if "
    "the submission has already been graded.",
    examples=[
        OpenApiExample(
            "Submit",
            value={"content_ref": "https://github.com/student/final-project"},
            request_only=True,
        ),
        OpenApiExample("Submitted", value=_ASSIGNMENT_SUBMISSION_EXAMPLE, response_only=True),
    ],
)
class AssignmentSubmissionCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        assignment = get_object_or_404(Assignment, pk=id)
        _require_enrollment(request.user, assignment.course_id)

        existing = AssignmentSubmission.objects.filter(
            assignment=assignment, student=request.user
        ).first()
        if existing is not None and existing.graded_at is not None:
            raise ValidationError("This assignment has already been graded; you cannot resubmit.")

        serializer = AssignmentSubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if existing is not None:
            existing.content_ref = serializer.validated_data["content_ref"]
            existing.submitted_at = timezone.now()
            existing.save(update_fields=["content_ref", "submitted_at"])
            submission, created = existing, False
        else:
            submission = AssignmentSubmission.objects.create(
                assignment=assignment, student=request.user, **serializer.validated_data
            )
            created = True

        record_event(
            actor=request.user,
            action="assignment_submission.create",
            entity_type="AssignmentSubmission",
            entity_id=submission.id,
            request=request,
        )
        return Response(
            AssignmentSubmissionSerializer(submission).data, status=201 if created else 200
        )


@extend_schema(
    tags=["Student"],
    responses={200: GradeEntrySerializer(many=True)},
    description="Lists the current user's completed quiz attempts and graded assignment "
    "submissions, combined into one grade list.",
    examples=[
        OpenApiExample(
            "Grades",
            value=[
                {
                    "type": "quiz",
                    "id": "f1e2d3c4-...",
                    "title": "Basics Quiz",
                    "score": 100.0,
                    "passed": True,
                    "submitted_at": "2026-02-01T10:05:00Z",
                },
                {
                    "type": "assignment",
                    "id": "c3d4e5f6-...",
                    "title": "Final Project",
                    "grade": 92,
                    "graded_at": "2026-02-01T09:00:00Z",
                },
            ],
            response_only=True,
        )
    ],
)
class MyGradesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        quiz_grades = [
            {
                "type": "quiz",
                "id": str(attempt.id),
                "title": attempt.quiz.title,
                "score": attempt.score,
                "passed": attempt.passed,
                "submitted_at": attempt.submitted_at,
            }
            for attempt in QuizAttempt.objects.filter(
                student=request.user, status=QuizAttempt.STATUS_SUBMITTED
            ).select_related("quiz")
        ]
        assignment_grades = [
            {
                "type": "assignment",
                "id": str(submission.id),
                "title": submission.assignment.title,
                "grade": submission.grade,
                "graded_at": submission.graded_at,
            }
            for submission in AssignmentSubmission.objects.filter(
                student=request.user, graded_at__isnull=False
            ).select_related("assignment")
        ]
        return Response(quiz_grades + assignment_grades)


# ---------- Coding exercises (student) ----------


_CODING_EXERCISE_EXAMPLE = {
    "id": "b2c3d4e5-...",
    "title": "Reverse a string",
    "prompt": "Write a function reverse(s) that returns s reversed.",
    "starter_code": "def reverse(s):\n    ...\n",
    "language": "python",
    "time_limit_ms": 2000,
    "memory_limit_mb": 128,
}


@extend_schema(
    tags=["Student"],
    responses={200: CodingExerciseDetailSerializer},
    description="Gets a coding exercise's prompt, starter code, and constraints for an "
    "enrolled student. Hidden test cases are never included.",
    examples=[OpenApiExample("Exercise", value=_CODING_EXERCISE_EXAMPLE, response_only=True)],
)
class CodingExerciseDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        exercise = get_object_or_404(CodingExercise, pk=id)
        _require_enrollment(request.user, exercise.course_id)
        return Response(CodingExerciseDetailSerializer(exercise).data)


@extend_schema(
    tags=["Student"],
    request=CodingExerciseSubmissionCreateSerializer,
    responses={202: CodingExerciseSubmissionSerializer},
    description="Submits source code for async judged execution (queued to Celery; poll "
    "GET .../submissions/{id}/ for the result). Only Python is judged today — other languages "
    "fail with 400.",
    examples=[
        OpenApiExample(
            "Submit code",
            value={"source_code": "def reverse(s):\n    return s[::-1]\n"},
            request_only=True,
        ),
        OpenApiExample(
            "Queued",
            value={
                "id": "e5f6a7b8-...",
                "status": "pending",
                "score": None,
                "runtime_ms": None,
                "results": None,
                "submitted_at": "2026-02-01T11:00:00Z",
                "graded_at": None,
            },
            response_only=True,
        ),
    ],
)
class CodingExerciseSubmissionCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        exercise = get_object_or_404(CodingExercise, pk=id)
        _require_enrollment(request.user, exercise.course_id)

        if exercise.language != CodingExercise.LANGUAGE_PYTHON:
            raise ValidationError(f"Judging for '{exercise.language}' is not implemented yet.")

        serializer = CodingExerciseSubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission = CodingExerciseSubmission.objects.create(
            coding_exercise=exercise,
            student=request.user,
            language=exercise.language,
            source_code=serializer.validated_data["source_code"],
        )
        judge_coding_submission.delay(str(submission.id))
        record_event(
            actor=request.user,
            action="coding_exercise_submission.create",
            entity_type="CodingExerciseSubmission",
            entity_id=submission.id,
            request=request,
        )
        return Response(CodingExerciseSubmissionSerializer(submission).data, status=202)


@extend_schema(
    tags=["Student"],
    responses={200: CodingExerciseSubmissionSerializer},
    description="Gets a coding submission's judged result — poll this after submitting until "
    "status is no longer 'pending'.",
    examples=[
        OpenApiExample(
            "Judged",
            value={
                "id": "e5f6a7b8-...",
                "status": "passed",
                "score": 100.0,
                "runtime_ms": 12,
                "results": [{"test_case": 1, "passed": True}],
                "submitted_at": "2026-02-01T11:00:00Z",
                "graded_at": "2026-02-01T11:00:05Z",
            },
            response_only=True,
        )
    ],
)
class CodingExerciseSubmissionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id, submission_id):
        submission = get_object_or_404(
            CodingExerciseSubmission, pk=submission_id, coding_exercise_id=id
        )
        if submission.student_id != request.user.id:
            raise PermissionDenied("Not your submission.")
        return Response(CodingExerciseSubmissionSerializer(submission).data)
