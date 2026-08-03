"""
Builds the real assessment content for each section: one Quiz (with
questions/answers), one Assignment, and — for a handful of sections — one
judged CodingExercise with test cases.
"""

from apps.assessments.models import (
    Answer,
    Assignment,
    CodingExercise,
    CodingExerciseTestCase,
    Question,
    Quiz,
)
from apps.catalog.models import Course
from apps.content.models import Section

from . import content_bank as cb


def build_quizzes(course: Course, sections_by_title: dict[str, dict]) -> list[Quiz]:
    quizzes = []
    for section_spec, quiz_spec in zip(cb.SECTIONS, cb.QUIZZES, strict=True):
        section: Section = sections_by_title[section_spec.title]["section"]

        quiz, _ = Quiz.objects.get_or_create(
            course=course,
            section=section,
            title=quiz_spec.title,
            defaults={
                "pass_score": quiz_spec.pass_score,
                "attempts_allowed": quiz_spec.attempts_allowed,
            },
        )
        quizzes.append(quiz)

        if quiz.questions.exists():
            continue  # already seeded on a previous run

        for question_index, question_spec in enumerate(quiz_spec.questions):
            question = Question.objects.create(
                quiz=quiz,
                type=Question.TYPE_SINGLE_CHOICE,
                prompt=question_spec.prompt,
                explanation=question_spec.explanation,
                sort_order=question_index,
            )
            Answer.objects.bulk_create(
                [
                    Answer(
                        question=question,
                        text=choice_text,
                        is_correct=(choice_index == question_spec.correct_index),
                        sort_order=choice_index,
                    )
                    for choice_index, choice_text in enumerate(question_spec.choices)
                ]
            )
    return quizzes


def build_assignments(course: Course) -> list[Assignment]:
    from django.utils import timezone

    assignments = []
    for assignment_spec in cb.ASSIGNMENTS:
        due_policy = {
            "due_at": (timezone.now() + timezone.timedelta(days=assignment_spec.due_in_days)).isoformat(),
            "allow_late": assignment_spec.allow_late,
        }
        assignment, created = Assignment.objects.get_or_create(
            course=course,
            title=assignment_spec.title,
            defaults={"instructions": assignment_spec.instructions, "due_policy": due_policy},
        )
        if not created:
            Assignment.objects.filter(pk=assignment.pk).update(instructions=assignment_spec.instructions)
        assignments.append(assignment)
    return assignments


def build_coding_exercises(course: Course, sections_by_title: dict[str, dict]) -> list[CodingExercise]:
    exercises = []
    for exercise_spec in cb.CODING_EXERCISES:
        section_spec = cb.SECTIONS[exercise_spec.section_index]
        section: Section = sections_by_title[section_spec.title]["section"]

        exercise, _ = CodingExercise.objects.get_or_create(
            course=course,
            section=section,
            title=exercise_spec.title,
            defaults={
                "prompt": exercise_spec.prompt,
                "starter_code": exercise_spec.starter_code,
                "language": CodingExercise.LANGUAGE_PYTHON,
            },
        )
        exercises.append(exercise)

        if exercise.test_cases.exists():
            continue

        CodingExerciseTestCase.objects.bulk_create(
            [
                CodingExerciseTestCase(
                    coding_exercise=exercise,
                    input=test_case.input,
                    expected_output=test_case.expected_output,
                    is_hidden=test_case.is_hidden,
                    weight=test_case.weight,
                )
                for test_case in exercise_spec.test_cases
            ]
        )
    return exercises
