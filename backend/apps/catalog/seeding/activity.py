"""
Builds realistic student activity around the seeded course: enrollments,
lesson progress, bookmarks/notes, quiz attempts + responses, assignment and
coding-exercise submissions, reviews, certificates, and wishlist entries.

Every bulk_create call below explicitly sets any auto_now/auto_now_add
field on the model — bulk_create bypasses Model.save(), which is where
Django normally populates those, so leaving them out would either insert
NULL (raising an IntegrityError) or silently skip the timestamp.

Idempotency: for each activity type, we compute the set of (student, target)
pairs that already exist and only bulk_create what's missing, so rerunning
the command is safe and additive rather than duplicating rows.
"""

import random
import uuid

from django.utils import timezone

from apps.assessments.models import (
    Answer,
    Assignment,
    AssignmentSubmission,
    CodingExercise,
    CodingExerciseSubmission,
    Question,
    Quiz,
    QuizAttempt,
    QuizResponse,
)
from apps.catalog.models import Course
from apps.content.models import Lesson
from apps.identity.models import User
from apps.learning.models import (
    Bookmark,
    Certificate,
    Enrollment,
    LessonNote,
    ProgressTracking,
    Wishlist,
    WishlistItem,
)
from apps.reviews.models import Review

from . import content_bank as cb

SEED_RNG_SEED = 20260728

COMPLETED_COUNT = 50
CERTIFICATE_COUNT = 10
REVIEW_COUNT = 20
WISHLIST_COUNT = 15
NOTE_TAKER_COUNT = 15


def _rng_for(*parts: str) -> random.Random:
    """A fresh RNG seeded from stable identifiers (e.g. a student's email),
    rather than one shared Random consumed sequentially across a loop.

    This matters for idempotency: a shared generator's exact output for
    student N depends on how many random draws happened for students
    0..N-1, which can shift between runs (e.g. if an unrelated code path
    consumes a different number of random calls). Seeding per-entity makes
    each student's/target's random choices depend only on its own stable
    key, so a rerun always recomputes the exact same values regardless of
    anything else that changed elsewhere in the pipeline.
    """
    return random.Random(":".join((str(SEED_RNG_SEED), *parts)))


def _flat_ordered_lessons(sections_by_title: dict[str, dict]) -> list[Lesson]:
    lessons: list[Lesson] = []
    for section_spec in cb.SECTIONS:
        lessons.extend(sections_by_title[section_spec.title]["lessons"])
    return lessons


def build_enrollments(
    course: Course, students: list[User]
) -> tuple[dict[uuid.UUID, Enrollment], list[User], list[User]]:
    """Enrolls every student. Returns (student_id -> Enrollment, completed_students,
    active_students)."""
    rng = random.Random(SEED_RNG_SEED)
    now = timezone.now()

    existing_student_ids = set(
        Enrollment.objects.filter(course=course).values_list("student_id", flat=True)
    )

    completed_students = students[:COMPLETED_COUNT]
    active_students = students[COMPLETED_COUNT:]

    new_enrollments: list[Enrollment] = []
    enrollment_by_student: dict[uuid.UUID, Enrollment] = {
        e.student_id: e
        for e in Enrollment.objects.filter(course=course).select_related(None)
    }

    for student in completed_students:
        if student.id in existing_student_ids:
            continue
        days_since_enrollment = rng.randint(45, 270)
        duration_to_complete = rng.randint(10, min(75, days_since_enrollment - 1))
        enrolled_at = now - timezone.timedelta(days=days_since_enrollment)
        completed_at = enrolled_at + timezone.timedelta(days=duration_to_complete)

        enrollment = Enrollment(
            course=course,
            student=student,
            source=rng.choices(
                [Enrollment.SOURCE_PURCHASE, Enrollment.SOURCE_DIRECT], weights=[0.85, 0.15]
            )[0],
            status=Enrollment.STATUS_COMPLETED,
            enrolled_at=enrolled_at,
            completed_at=completed_at,
        )
        new_enrollments.append(enrollment)
        enrollment_by_student[student.id] = enrollment

    for student in active_students:
        if student.id in existing_student_ids:
            continue
        enrolled_at = now - timezone.timedelta(days=rng.randint(3, 120))
        enrollment = Enrollment(
            course=course,
            student=student,
            source=rng.choices(
                [Enrollment.SOURCE_PURCHASE, Enrollment.SOURCE_DIRECT], weights=[0.85, 0.15]
            )[0],
            status=Enrollment.STATUS_ACTIVE,
            enrolled_at=enrolled_at,
            completed_at=None,
        )
        new_enrollments.append(enrollment)
        enrollment_by_student[student.id] = enrollment

    if new_enrollments:
        Enrollment.objects.bulk_create(new_enrollments)

    return enrollment_by_student, completed_students, active_students


def build_progress(
    course: Course,
    sections_by_title: dict[str, dict],
    enrollment_by_student: dict[uuid.UUID, Enrollment],
    completed_students: list[User],
    active_students: list[User],
) -> None:
    now = timezone.now()
    all_lessons = _flat_ordered_lessons(sections_by_title)

    existing_pairs = set(
        ProgressTracking.objects.filter(enrollment__course=course).values_list(
            "enrollment_id", "lesson_id"
        )
    )

    new_entries: list[ProgressTracking] = []

    for student in completed_students:
        enrollment = enrollment_by_student[student.id]
        last_viewed = enrollment.completed_at or now
        for lesson in all_lessons:
            if (enrollment.id, lesson.id) in existing_pairs:
                continue
            new_entries.append(
                ProgressTracking(
                    enrollment=enrollment,
                    lesson=lesson,
                    percent_complete=100,
                    last_position_seconds=lesson.duration_seconds,
                    last_viewed_at=last_viewed,
                )
            )

    for student in active_students:
        rng = _rng_for("progress", student.email)
        enrollment = enrollment_by_student[student.id]
        watched_count = rng.randint(10, min(60, len(all_lessons)))
        watched_lessons = all_lessons[:watched_count]
        last_viewed = min(enrollment.enrolled_at + timezone.timedelta(days=rng.randint(1, 30)), now)

        for position, lesson in enumerate(watched_lessons):
            if (enrollment.id, lesson.id) in existing_pairs:
                continue
            is_current_lesson = position == watched_count - 1
            percent = rng.randint(10, 90) if is_current_lesson else 100
            new_entries.append(
                ProgressTracking(
                    enrollment=enrollment,
                    lesson=lesson,
                    percent_complete=percent,
                    last_position_seconds=round(lesson.duration_seconds * percent / 100),
                    last_viewed_at=last_viewed,
                )
            )

    for chunk_start in range(0, len(new_entries), 2000):
        ProgressTracking.objects.bulk_create(new_entries[chunk_start : chunk_start + 2000])


def build_bookmarks_and_notes(
    sections_by_title: dict[str, dict],
    active_students: list[User],
    enrollment_by_student: dict[uuid.UUID, Enrollment],
) -> None:
    all_lessons = _flat_ordered_lessons(sections_by_title)
    note_takers = active_students[:NOTE_TAKER_COUNT]

    note_texts = [
        "Re-watch the part about {topic} before the assignment — went a bit fast.",
        "Good real-world example here of {topic}. Want to try this in my own project.",
        "Question for office hours: how does {topic} interact with the previous lesson?",
        "This is the bit that finally made {topic} click for me.",
        "Need to review {topic} again — took two passes to fully follow.",
    ]

    existing_bookmark_keys = set(Bookmark.objects.values_list("student_id", "lesson_id"))
    existing_note_keys = set(LessonNote.objects.values_list("student_id", "lesson_id"))

    new_bookmarks: list[Bookmark] = []
    new_notes: list[LessonNote] = []

    for student in note_takers:
        rng = _rng_for("bookmarks", student.email)
        enrollment = enrollment_by_student[student.id]
        sample_size = min(3, len(all_lessons))
        for lesson in rng.sample(all_lessons, sample_size):
            timestamp = rng.randint(30, max(31, lesson.duration_seconds - 30))
            created_at = min(
                enrollment.enrolled_at + timezone.timedelta(days=rng.randint(1, 20)), timezone.now()
            )

            if (student.id, lesson.id) not in existing_bookmark_keys:
                new_bookmarks.append(
                    Bookmark(
                        lesson=lesson,
                        student=student,
                        timestamp_seconds=timestamp,
                        label=lesson.title[:60],
                        created_at=created_at,
                    )
                )
            if (student.id, lesson.id) not in existing_note_keys:
                topic = lesson.title.rstrip(".")
                new_notes.append(
                    LessonNote(
                        lesson=lesson,
                        student=student,
                        note_text=rng.choice(note_texts).format(topic=topic),
                        timestamp_seconds=timestamp,
                        created_at=created_at,
                    )
                )

    if new_bookmarks:
        Bookmark.objects.bulk_create(new_bookmarks)
    if new_notes:
        LessonNote.objects.bulk_create(new_notes)


def build_quiz_attempts(
    quizzes: list[Quiz],
    completed_students: list[User],
    enrollment_by_student: dict[uuid.UUID, Enrollment],
) -> None:
    rng = random.Random(SEED_RNG_SEED)

    existing_pairs = set(
        QuizAttempt.objects.filter(status=QuizAttempt.STATUS_SUBMITTED).values_list(
            "quiz_id", "student_id"
        )
    )

    questions_by_quiz: dict[uuid.UUID, list[Question]] = {
        quiz.id: list(quiz.questions.prefetch_related("answers").all()) for quiz in quizzes
    }

    new_attempts: list[QuizAttempt] = []
    # (attempt, ordered list of (question, is_correct)) so responses can be
    # built after the attempts are inserted and their pks are known.
    pending_responses: list[tuple[QuizAttempt, list[tuple[Question, bool]]]] = []

    for student in completed_students:
        enrollment = enrollment_by_student[student.id]
        window_end = enrollment.completed_at or timezone.now()

        for quiz in quizzes:
            if (quiz.id, student.id) in existing_pairs:
                continue
            questions = questions_by_quiz[quiz.id]
            if not questions:
                continue

            score = rng.randint(60, 100)
            correct_count = round(len(questions) * score / 100)
            correct_count = min(correct_count, len(questions))
            shuffled = questions[:]
            rng.shuffle(shuffled)
            correct_flags = {q.id: False for q in questions}
            for question in shuffled[:correct_count]:
                correct_flags[question.id] = True

            started_at = enrollment.enrolled_at + timezone.timedelta(
                days=rng.randint(0, max(0, (window_end - enrollment.enrolled_at).days))
            )
            submitted_at = started_at + timezone.timedelta(minutes=rng.randint(4, 25))

            attempt = QuizAttempt(
                quiz=quiz,
                student=student,
                status=QuizAttempt.STATUS_SUBMITTED,
                started_at=started_at,
                submitted_at=submitted_at,
                score=float(score),
                passed=score >= quiz.pass_score,
            )
            new_attempts.append(attempt)
            pending_responses.append(
                (attempt, [(question, correct_flags[question.id]) for question in questions])
            )

    if not new_attempts:
        return

    QuizAttempt.objects.bulk_create(new_attempts)

    new_responses: list[QuizResponse] = []
    response_answer_map: list[tuple[QuizResponse, list[Answer]]] = []

    for attempt, question_flags in pending_responses:
        for question, is_correct in question_flags:
            answers = list(question.answers.all())
            correct_answer = next((a for a in answers if a.is_correct), None)
            wrong_answers = [a for a in answers if not a.is_correct]

            if is_correct and correct_answer is not None:
                chosen = [correct_answer]
            elif wrong_answers:
                chosen = [rng.choice(wrong_answers)]
            else:
                chosen = []

            response = QuizResponse(attempt=attempt, question=question, is_correct=is_correct)
            new_responses.append(response)
            response_answer_map.append((response, chosen))

    for chunk_start in range(0, len(new_responses), 2000):
        QuizResponse.objects.bulk_create(new_responses[chunk_start : chunk_start + 2000])

    for response, chosen_answers in response_answer_map:
        if chosen_answers:
            response.selected_answers.set(chosen_answers)


def build_assignment_submissions(
    assignments: list[Assignment],
    completed_students: list[User],
    enrollment_by_student: dict[uuid.UUID, Enrollment],
    instructor: User,
) -> None:
    rng = random.Random(SEED_RNG_SEED)
    feedback_pool = [
        "Solid work overall — clean structure and good separation of concerns.",
        "Meets all requirements. Minor style nitpicks only, nothing blocking.",
        "Nice job handling the edge cases. Consider adding a few more tests next time.",
        "Well organized submission. The README made it easy to review.",
        "Good attempt at the core requirement. Double-check naming conventions going forward.",
    ]

    existing_pairs = set(
        AssignmentSubmission.objects.values_list("assignment_id", "student_id")
    )

    new_submissions: list[AssignmentSubmission] = []
    for student in completed_students:
        local_part = student.email.split("@")[0]
        enrollment = enrollment_by_student[student.id]
        window_end = enrollment.completed_at or timezone.now()

        for index, assignment in enumerate(assignments):
            if (assignment.id, student.id) in existing_pairs:
                continue
            submitted_at = enrollment.enrolled_at + timezone.timedelta(
                days=rng.randint(1, max(1, (window_end - enrollment.enrolled_at).days))
            )
            graded_at = submitted_at + timezone.timedelta(days=rng.randint(1, 3))
            grade = float(rng.randint(72, 100))

            new_submissions.append(
                AssignmentSubmission(
                    assignment=assignment,
                    student=student,
                    content_ref=(
                        f"https://github.com/{local_part}/mastering-django-coursework/"
                        f"tree/main/section-{index + 1:02d}"
                    ),
                    grade=grade,
                    feedback=rng.choice(feedback_pool),
                    graded_by=instructor,
                    graded_at=graded_at,
                    submitted_at=submitted_at,
                )
            )

    for chunk_start in range(0, len(new_submissions), 2000):
        AssignmentSubmission.objects.bulk_create(new_submissions[chunk_start : chunk_start + 2000])


def build_coding_exercise_submissions(
    exercises: list[CodingExercise],
    completed_students: list[User],
    enrollment_by_student: dict[uuid.UUID, Enrollment],
) -> None:
    rng = random.Random(SEED_RNG_SEED)
    submitters = completed_students[:30]

    existing_pairs = set(
        CodingExerciseSubmission.objects.values_list("coding_exercise_id", "student_id")
    )

    new_submissions: list[CodingExerciseSubmission] = []
    for student in submitters:
        enrollment = enrollment_by_student[student.id]
        window_end = enrollment.completed_at or timezone.now()

        for exercise in exercises:
            if (exercise.id, student.id) in existing_pairs:
                continue
            submitted_at = enrollment.enrolled_at + timezone.timedelta(
                days=rng.randint(1, max(1, (window_end - enrollment.enrolled_at).days))
            )
            test_case_count = exercise.test_cases.count() or 2
            new_submissions.append(
                CodingExerciseSubmission(
                    coding_exercise=exercise,
                    student=student,
                    source_code=exercise.starter_code + "\n# Solved during the course.\n",
                    language=CodingExercise.LANGUAGE_PYTHON,
                    status=CodingExerciseSubmission.STATUS_PASSED,
                    score=100.0,
                    runtime_ms=rng.randint(20, 250),
                    result_detail=[
                        {"is_hidden": i >= (test_case_count - 1), "passed": True}
                        for i in range(test_case_count)
                    ],
                    submitted_at=submitted_at,
                    graded_at=submitted_at,
                )
            )

    for chunk_start in range(0, len(new_submissions), 2000):
        CodingExerciseSubmission.objects.bulk_create(new_submissions[chunk_start : chunk_start + 2000])


def build_reviews(
    course: Course,
    completed_students: list[User],
    enrollment_by_student: dict[uuid.UUID, Enrollment],
) -> None:
    # A fixed top-N slice (mirroring build_certificates) rather than "the next
    # N students without a review yet" — the latter keeps advancing through
    # completed_students on every rerun, adding REVIEW_COUNT more reviews
    # each time instead of converging on a stable total of REVIEW_COUNT.
    existing_reviewer_ids = set(Review.objects.filter(course=course).values_list("user_id", flat=True))
    reviewers = completed_students[:REVIEW_COUNT]

    new_reviews: list[Review] = []
    for student, (rating, text) in zip(reviewers, cb.REVIEWS, strict=False):
        if student.id in existing_reviewer_ids:
            continue
        enrollment = enrollment_by_student[student.id]
        created_at = (enrollment.completed_at or timezone.now()) + timezone.timedelta(days=1)
        new_reviews.append(
            Review(
                course=course,
                user=student,
                rating=rating,
                review_text=text,
                is_verified_purchase=True,
                created_at=created_at,
                updated_at=created_at,
            )
        )

    if new_reviews:
        Review.objects.bulk_create(new_reviews)


def build_certificates(
    completed_students: list[User], enrollment_by_student: dict[uuid.UUID, Enrollment]
) -> None:
    existing_enrollment_ids = set(Certificate.objects.values_list("enrollment_id", flat=True))
    recipients = completed_students[:CERTIFICATE_COUNT]

    new_certificates: list[Certificate] = []
    for student in recipients:
        enrollment = enrollment_by_student[student.id]
        if enrollment.id in existing_enrollment_ids:
            continue
        certificate_uid = f"CERT-{uuid.uuid4().hex[:16].upper()}"
        issued_at = (enrollment.completed_at or timezone.now()) + timezone.timedelta(days=1)
        new_certificates.append(
            Certificate(
                enrollment=enrollment,
                certificate_uid=certificate_uid,
                qr_payload=f"https://skillchain.example.com/verify/{certificate_uid}",
                issued_at=issued_at,
            )
        )

    if new_certificates:
        Certificate.objects.bulk_create(new_certificates)


def build_wishlist(course: Course, active_students: list[User]) -> None:
    for student in active_students[:WISHLIST_COUNT]:
        wishlist, _ = Wishlist.objects.get_or_create(user=student)
        WishlistItem.objects.get_or_create(wishlist=wishlist, course=course)
