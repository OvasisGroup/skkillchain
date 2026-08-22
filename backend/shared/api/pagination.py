from rest_framework.pagination import CursorPagination


class DefaultCursorPagination(CursorPagination):
    """
    Global default (see REST_FRAMEWORK.DEFAULT_PAGINATION_CLASS) — stable
    under concurrent inserts to the underlying list, unlike offset/limit
    pagination. `ordering` is a sane default for most of this project's
    list endpoints; override per-view (e.g. course search relevance
    ranking) where "newest first" isn't the right cursor field.
    """

    page_size = 20
    max_page_size = 100
    ordering = "-created_at"
    cursor_query_param = "cursor"


class EnrolledAtCursorPagination(DefaultCursorPagination):
    """For models with `enrolled_at` instead of `created_at` (Enrollment)."""

    ordering = "-enrolled_at"


class IssuedAtCursorPagination(DefaultCursorPagination):
    """For models with `issued_at` instead of `created_at` (Certificate)."""

    ordering = "-issued_at"


class StartedAtCursorPagination(DefaultCursorPagination):
    """For models with `started_at` instead of `created_at` (AiChatSession)."""

    ordering = "-started_at"


class AppliedAtCursorPagination(DefaultCursorPagination):
    """For models with `applied_at` instead of `created_at` (InstructorApplication)."""

    ordering = "-applied_at"


class RequestedAtCursorPagination(DefaultCursorPagination):
    """For models with `requested_at` instead of `created_at` (DataErasureRequest)."""

    ordering = "-requested_at"


class StartsAtCursorPagination(DefaultCursorPagination):
    """For Hackathon browsing ordered by start time, soonest first (active/
    upcoming lists) rather than newest-created first."""

    ordering = "starts_at"


class EndsAtDescCursorPagination(DefaultCursorPagination):
    """For Hackathon "completed" lists — most recently finished first."""

    ordering = "-ends_at"


class RegisteredAtCursorPagination(DefaultCursorPagination):
    """For models with `registered_at` instead of `created_at`
    (HackathonRegistration)."""

    ordering = "-registered_at"


class PublishedAtCursorPagination(DefaultCursorPagination):
    """For the public BlogPost list — newest published first. Only ever
    applied to an already-published-only queryset, so `published_at` is
    never null (see BlogPostListView)."""

    ordering = "-published_at"


class SortOrderCursorPagination(DefaultCursorPagination):
    """For curriculum models ordered by instructor-assigned position rather than
    creation time (Section, Lesson) — ascending, since these are read in the
    order a student progresses through them, not newest-first."""

    ordering = "sort_order"
