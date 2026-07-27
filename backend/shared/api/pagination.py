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
