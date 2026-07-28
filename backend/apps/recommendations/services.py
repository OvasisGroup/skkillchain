from django.db.models import Case, Count, IntegerField, Q, When

from apps.catalog.models import Category, Course

_DIFFICULTY_ORDER = Case(
    When(difficulty=Course.DIFFICULTY_BEGINNER, then=0),
    When(difficulty=Course.DIFFICULTY_INTERMEDIATE, then=1),
    When(difficulty=Course.DIFFICULTY_ADVANCED, then=2),
    default=3,
    output_field=IntegerField(),
)


def _enrolled_course_ids(user) -> list:
    return list(Course.objects.filter(enrollments__student=user).values_list("id", flat=True))


def _engaged_category_ids(enrolled_course_ids: list) -> list:
    return list(
        Category.objects.filter(courses__id__in=enrolled_course_ids)
        .values_list("id", flat=True)
        .distinct()
    )


def _candidate_courses(user):
    # Real (non-ML) heuristic: courses in categories the student has
    # already engaged with, excluding what they're already enrolled in.
    # analytics_events (M10) doesn't exist yet — once it does, this is the
    # natural place to weight by view/click events instead of just
    # enrollment history, not a blocker for building this now.
    enrolled_course_ids = _enrolled_course_ids(user)
    engaged_category_ids = _engaged_category_ids(enrolled_course_ids)

    qs = Course.objects.filter(status=Course.STATUS_PUBLISHED).exclude(id__in=enrolled_course_ids)
    if engaged_category_ids:
        qs = qs.filter(categories__id__in=engaged_category_ids)
    return qs.annotate(enrollment_count=Count("enrollments")).distinct()


def recommended_courses(user, limit: int = 10):
    # Cold-start (no engaged categories): falls back to the platform's
    # most-enrolled published courses overall, via the same queryset —
    # _candidate_courses only applies the category filter when there's
    # history to filter by.
    return _candidate_courses(user).order_by("-enrollment_count")[:limit]


def learning_path_courses(user, limit: int = 10):
    # "Learning path" ordering: CoursePrerequisite is free text, not a
    # course-to-course graph (confirmed in apps.catalog.models), so there's
    # no real prerequisite chain to walk. This orders the same candidate
    # set by difficulty (beginner -> advanced) within the student's
    # engaged categories, then popularity — a genuine, simple path rather
    # than a fabricated dependency graph.
    return (
        _candidate_courses(user)
        .annotate(difficulty_order=_DIFFICULTY_ORDER)
        .order_by("difficulty_order", "-enrollment_count")[:limit]
    )


def search_courses(query: str, limit: int = 20):
    # Plain text search — no vector store/embeddings infra exists anywhere
    # in this stack, so true semantic search is out of scope here.
    return (
        Course.objects.filter(status=Course.STATUS_PUBLISHED)
        .filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(description__icontains=query)
        )
        .distinct()[:limit]
    )
