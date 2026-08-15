"""
Builds the Course, its Category/Tag attachments, prerequisites/objectives,
and the full Section -> Lesson curriculum tree. Also drives the Course
through its real draft -> submitted -> approved -> published lifecycle so it
behaves exactly like an instructor-authored, platform-approved course.
"""

import random

from apps.catalog.models import (
    Category,
    Course,
    CourseLearningObjective,
    CoursePrerequisite,
)
from apps.content.models import Lesson, Section
from apps.identity.models import User

from . import content_bank as cb

# Video lessons get a randomized runtime in this range, then the whole batch
# is scaled up (never down) so the course always clears the advertised 80+
# hour total regardless of how the random draw lands.
VIDEO_DURATION_RANGE = (900, 2100)  # 15-35 minutes
ARTICLE_DURATION_RANGE = (900, 1800)  # 15-30 minutes (hands-on practice)
MARKER_DURATION = 300  # "review the brief" time for quiz/assignment marker lessons
TARGET_TOTAL_SECONDS = 80 * 3600  # the advertised "80+ Hours"

SEED_RNG_SEED = 20260728


def get_or_create_categories() -> Category:
    """Returns the 'Backend Development' child category (course-facing),
    nested under a 'Programming' parent."""
    parent, _ = Category.objects.get_or_create(
        slug="programming", defaults={"name": cb.CATEGORY_PARENT_NAME}
    )
    child, _ = Category.objects.get_or_create(
        slug="backend-development",
        defaults={"name": cb.CATEGORY_CHILD_NAME, "parent": parent},
    )
    if child.parent_id != parent.id:
        child.parent = parent
        child.save(update_fields=["parent"])
    return child


def get_or_create_tags() -> list:
    from apps.catalog.models import Tag

    tags = []
    for name, slug in cb.TAGS:
        tag, _ = Tag.objects.get_or_create(slug=slug, defaults={"name": name})
        tags.append(tag)
    return tags


def get_or_create_course(instructor: User) -> Course:
    course, created = Course.objects.get_or_create(
        slug="mastering-django-beginner-to-enterprise",
        defaults={
            "owner": instructor,
            "title": cb.COURSE_TITLE,
            "summary": cb.COURSE_SUMMARY,
            "description": cb.COURSE_DESCRIPTION,
            "language": cb.LANGUAGE,
            "difficulty": Course.DIFFICULTY_BEGINNER,
            "price_amount": cb.PRICE_AMOUNT,
            "currency": cb.CURRENCY,
        },
    )
    if not created:
        # Keep authored fields in sync on rerun without touching lifecycle state.
        Course.objects.filter(pk=course.pk).update(
            summary=cb.COURSE_SUMMARY,
            description=cb.COURSE_DESCRIPTION,
            price_amount=cb.PRICE_AMOUNT,
            currency=cb.CURRENCY,
        )
        course.refresh_from_db()

    category = get_or_create_categories()
    if course.category_id != category.id:
        course.category = category
        course.save(update_fields=["category"])
    course.tags.set(get_or_create_tags())

    for text in cb.PREREQUISITES:
        CoursePrerequisite.objects.get_or_create(course=course, text=text)
    for text in cb.LEARNING_OBJECTIVES:
        CourseLearningObjective.objects.get_or_create(course=course, text=text)

    _advance_to_published(course)
    return course


def _advance_to_published(course: Course) -> None:
    """Drives the course through its real lifecycle methods rather than
    setting `status` directly, so it ends up published the same way a real
    instructor submission + platform approval would."""
    if course.status == Course.STATUS_DRAFT:
        course.submit_for_review()
    if course.status == Course.STATUS_SUBMITTED:
        course.approve()
    if course.status == Course.STATUS_APPROVED:
        course.publish()


def build_sections_and_lessons(course: Course) -> dict[str, dict]:
    """Creates every Section and Lesson from content_bank.SECTIONS.

    Returns a lookup keyed by section title with the Section instance and its
    ordered list of Lesson instances, so downstream builders (quizzes,
    assignments, coding exercises, progress) can find "the video lessons for
    section N" without re-querying.
    """
    rng = random.Random(SEED_RNG_SEED)
    result: dict[str, dict] = {}

    for section_index, section_spec in enumerate(cb.SECTIONS):
        section, _ = Section.objects.get_or_create(
            course=course,
            title=section_spec.title,
            defaults={"sort_order": section_index},
        )
        if section.sort_order != section_index:
            section.sort_order = section_index
            section.save(update_fields=["sort_order"])

        lessons: list[Lesson] = []
        video_lessons: list[Lesson] = []
        for lesson_index, lesson_spec in enumerate(section_spec.lessons):
            if lesson_spec.kind == "video":
                duration = rng.randint(*VIDEO_DURATION_RANGE)
            elif lesson_spec.kind == "article":
                duration = rng.randint(*ARTICLE_DURATION_RANGE)
            else:
                duration = MARKER_DURATION

            lesson, _ = Lesson.objects.get_or_create(
                section=section,
                title=lesson_spec.title,
                defaults={
                    "lesson_type": lesson_spec.kind,
                    "sort_order": lesson_index,
                    "duration_seconds": duration,
                    "is_preview": lesson_spec.is_preview,
                },
            )
            # Keep ordering/type/preview flags in sync on rerun; duration is
            # only set at creation so reruns don't perturb progress data that
            # references a lesson's original duration.
            changed_fields = []
            if lesson.sort_order != lesson_index:
                lesson.sort_order = lesson_index
                changed_fields.append("sort_order")
            if lesson.lesson_type != lesson_spec.kind:
                lesson.lesson_type = lesson_spec.kind
                changed_fields.append("lesson_type")
            if lesson.is_preview != lesson_spec.is_preview:
                lesson.is_preview = lesson_spec.is_preview
                changed_fields.append("is_preview")
            if changed_fields:
                lesson.save(update_fields=changed_fields)

            lessons.append(lesson)
            if lesson_spec.kind == "video":
                video_lessons.append(lesson)

        result[section_spec.title] = {
            "section": section,
            "lessons": lessons,
            "video_lessons": video_lessons,
        }

    _normalize_total_duration(result)
    return result


def _normalize_total_duration(sections_by_title: dict[str, dict]) -> None:
    """Scales up video-lesson durations (proportionally) if the randomized
    total falls short of the advertised 80+ hour course length. Never scales
    down — a random draw landing above target is left alone."""
    all_video_lessons = [
        lesson for entry in sections_by_title.values() for lesson in entry["video_lessons"]
    ]
    total_seconds = sum(
        lesson.duration_seconds
        for entry in sections_by_title.values()
        for lesson in entry["lessons"]
    )
    if total_seconds >= TARGET_TOTAL_SECONDS or not all_video_lessons:
        return

    deficit = TARGET_TOTAL_SECONDS - total_seconds
    per_lesson_bump = -(-deficit // len(all_video_lessons))  # ceil division

    updated = []
    for lesson in all_video_lessons:
        lesson.duration_seconds += per_lesson_bump
        updated.append(lesson)
    Lesson.objects.bulk_update(updated, ["duration_seconds"])
