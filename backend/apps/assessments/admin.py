from django.contrib import admin

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


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "attempts_allowed", "pass_score"]
    search_fields = ["title", "course__title"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["prompt", "quiz", "type"]
    search_fields = ["prompt", "quiz__title"]
    inlines = [AnswerInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ["student", "quiz", "status", "score", "passed", "started_at"]
    list_filter = ["status", "passed"]
    search_fields = ["student__email", "quiz__title"]
    readonly_fields = ["id", "started_at"]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["title", "course"]
    search_fields = ["title", "course__title"]


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ["student", "assignment", "grade", "graded_at", "submitted_at"]
    list_filter = ["assignment"]
    search_fields = ["student__email", "assignment__title"]
    readonly_fields = ["id", "submitted_at"]


class CodingExerciseTestCaseInline(admin.TabularInline):
    model = CodingExerciseTestCase
    extra = 0


@admin.register(CodingExercise)
class CodingExerciseAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "language", "time_limit_ms", "memory_limit_mb"]
    search_fields = ["title", "course__title"]
    inlines = [CodingExerciseTestCaseInline]


@admin.register(CodingExerciseSubmission)
class CodingExerciseSubmissionAdmin(admin.ModelAdmin):
    list_display = ["student", "coding_exercise", "status", "score", "runtime_ms", "submitted_at"]
    list_filter = ["status"]
    search_fields = ["student__email", "coding_exercise__title"]
    readonly_fields = ["id", "submitted_at", "result_detail"]
