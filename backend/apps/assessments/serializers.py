from rest_framework import serializers

from .models import (
    Answer,
    Assignment,
    AssignmentSubmission,
    CodingExercise,
    CodingExerciseSubmission,
    CodingExerciseTestCase,
    Question,
    Quiz,
    QuizAttempt,
)


class AnswerOptionSerializer(serializers.ModelSerializer):
    """Never includes is_correct — used everywhere a student picks an
    answer, before grading has happened."""

    class Meta:
        model = Answer
        fields = ["id", "text", "sort_order"]


class QuestionForAttemptSerializer(serializers.ModelSerializer):
    answers = AnswerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "type", "prompt", "sort_order", "answers"]


class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuestionForAttemptSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "attempts_allowed", "pass_score", "questions"]


class AnswerWriteSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=500)
    is_correct = serializers.BooleanField(default=False)
    sort_order = serializers.IntegerField(default=0)


class QuestionWriteSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=Question.TYPE_CHOICES, default=Question.TYPE_SINGLE_CHOICE
    )
    prompt = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_blank=True, default="")
    sort_order = serializers.IntegerField(default=0)
    answers = AnswerWriteSerializer(many=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("A question needs at least one answer.")
        if not any(a["is_correct"] for a in value):
            raise serializers.ValidationError("A question needs at least one correct answer.")
        return value


class QuizCreateSerializer(serializers.ModelSerializer):
    questions = QuestionWriteSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "attempts_allowed", "pass_score", "section", "questions"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        quiz = Quiz.objects.create(**validated_data)
        for question_data in questions_data:
            answers_data = question_data.pop("answers")
            question = Question.objects.create(quiz=quiz, **question_data)
            for answer_data in answers_data:
                Answer.objects.create(question=question, **answer_data)
        return quiz


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ["id", "quiz", "status", "started_at", "submitted_at", "score", "passed"]


class QuizResponseInputSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    answer_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=True)


class QuizSubmitSerializer(serializers.Serializer):
    responses = QuizResponseInputSerializer(many=True)


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ["id", "course", "title", "instructions", "due_policy"]


class AssignmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ["id", "title", "instructions", "due_policy"]
        read_only_fields = ["id"]


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.email", read_only=True)

    class Meta:
        model = AssignmentSubmission
        fields = [
            "id",
            "assignment",
            "student_email",
            "content_ref",
            "grade",
            "feedback",
            "graded_at",
            "submitted_at",
        ]


class AssignmentSubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = ["content_ref"]


class AssignmentGradeSerializer(serializers.Serializer):
    grade = serializers.FloatField(min_value=0, max_value=100)
    feedback = serializers.CharField(required=False, allow_blank=True)


class CodingExerciseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodingExercise
        fields = [
            "id",
            "title",
            "prompt",
            "starter_code",
            "language",
            "time_limit_ms",
            "memory_limit_mb",
        ]


class TestCaseWriteSerializer(serializers.Serializer):
    input = serializers.CharField(required=False, allow_blank=True, default="")
    expected_output = serializers.CharField()
    is_hidden = serializers.BooleanField(default=True)
    weight = serializers.IntegerField(default=1, min_value=1)


class CodingExerciseCreateSerializer(serializers.ModelSerializer):
    test_cases = TestCaseWriteSerializer(many=True, write_only=True)

    class Meta:
        model = CodingExercise
        fields = [
            "id",
            "title",
            "prompt",
            "starter_code",
            "language",
            "time_limit_ms",
            "memory_limit_mb",
            "section",
            "test_cases",
        ]
        read_only_fields = ["id"]

    def validate_test_cases(self, value):
        if not value:
            raise serializers.ValidationError("A coding exercise needs at least one test case.")
        return value

    def create(self, validated_data):
        test_cases_data = validated_data.pop("test_cases")
        exercise = CodingExercise.objects.create(**validated_data)
        for test_case_data in test_cases_data:
            CodingExerciseTestCase.objects.create(coding_exercise=exercise, **test_case_data)
        return exercise


class CodingExerciseSubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodingExerciseSubmission
        # language is deliberately not client-settable — it's copied from
        # the exercise itself so a submission can't claim to be a
        # different language than what it's actually judged as.
        fields = ["source_code"]


class CodingExerciseSubmissionSerializer(serializers.ModelSerializer):
    results = serializers.JSONField(source="result_detail", read_only=True)

    class Meta:
        model = CodingExerciseSubmission
        fields = ["id", "status", "score", "runtime_ms", "results", "submitted_at", "graded_at"]


GRADE_ENTRY_TYPE_CHOICES = [("quiz", "Quiz"), ("assignment", "Assignment")]


class GradeEntrySerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=GRADE_ENTRY_TYPE_CHOICES)
    id = serializers.CharField()
    title = serializers.CharField()
    score = serializers.FloatField(required=False, allow_null=True)
    passed = serializers.BooleanField(required=False, allow_null=True)
    grade = serializers.FloatField(required=False, allow_null=True)
    submitted_at = serializers.DateTimeField(required=False, allow_null=True)
    graded_at = serializers.DateTimeField(required=False, allow_null=True)
