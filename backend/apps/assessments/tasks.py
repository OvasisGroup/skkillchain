import logging

from celery import shared_task
from django.utils import timezone

from . import judge
from .models import CodingExercise, CodingExerciseSubmission

logger = logging.getLogger(__name__)


@shared_task(name="assessments.judge_coding_submission", time_limit=120)
def judge_coding_submission(submission_id: str) -> str:
    """
    Runs a coding-exercise submission against its exercise's test cases and
    records the graded result. Dispatched from the submission-create view
    so a slow/hung submission never blocks the request — see judge.py for
    the sandbox's real (limited) isolation guarantees.
    """
    submission = CodingExerciseSubmission.objects.select_related("coding_exercise").get(
        id=submission_id
    )
    submission.status = CodingExerciseSubmission.STATUS_RUNNING
    submission.save(update_fields=["status"])

    exercise: CodingExercise = submission.coding_exercise
    test_cases = list(exercise.test_cases.all())

    if not test_cases:
        submission.status = CodingExerciseSubmission.STATUS_ERROR
        submission.result_detail = []
        submission.graded_at = timezone.now()
        submission.save(update_fields=["status", "result_detail", "graded_at"])
        logger.warning("assessments.judge_coding_submission: %s has no test cases", exercise.id)
        return submission.status

    outcome = judge.grade_submission(
        submission.source_code,
        test_cases,
        time_limit_ms=exercise.time_limit_ms,
        memory_limit_mb=exercise.memory_limit_mb,
    )

    submission.status = outcome["status"]
    submission.score = outcome["score"]
    submission.runtime_ms = outcome["runtime_ms"]
    submission.result_detail = outcome["results"]
    submission.graded_at = timezone.now()
    submission.save(update_fields=["status", "score", "runtime_ms", "result_detail", "graded_at"])
    return submission.status
