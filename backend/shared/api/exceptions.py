from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.views import exception_handler as drf_exception_handler

from apps.audit.services import record_event

_PROBLEM_BASE = "https://api.skillchain.com/problems"


def rfc7807_exception_handler(exc, context):
    """
    Converts every DRF exception into an RFC 7807 problem+json body (see
    docs/03-api/01-api-documentation.md §15) and audit-logs access-denied
    responses so a 403 is provably traceable without every view remembering
    to log it itself.
    """
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, (PermissionDenied, NotAuthenticated)):
        _log_access_denied(exc, context)

    original = response.data
    problem = {
        "type": f"{_PROBLEM_BASE}/{exc.__class__.__name__.lower()}",
        "title": getattr(exc, "default_detail", exc.__class__.__name__),
        "status": response.status_code,
    }
    if isinstance(original, dict) and set(original.keys()) == {"detail"}:
        problem["detail"] = str(original["detail"])
    else:
        problem["errors"] = original

    response.data = problem
    # Response.rendered_content builds the Content-Type header from
    # self.content_type (if set) before falling back to the negotiated
    # renderer's own media_type — and unlike accepted_media_type, DRF's
    # finalize_response() never touches content_type, so setting it here
    # actually survives to the wire.
    response.content_type = "application/problem+json"
    return response


def _log_access_denied(exc, context):
    request = context.get("request")
    view = context.get("view")
    actor = getattr(request, "user", None)
    record_event(
        actor=actor if actor is not None and actor.is_authenticated else None,
        action="access.denied",
        entity_type=view.__class__.__name__ if view else "",
        request=request,
        payload={"detail": str(exc)},
    )
