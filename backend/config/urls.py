from django.conf import settings
from django.contrib import admin
from django.http import Http404
from django.urls import include, path, re_path
from django.views.defaults import page_not_found
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", include("shared.health.urls")),
    path("api/v1/auth/", include("apps.identity.urls")),
    path("api/v1/", include("apps.identity.admin_urls")),
    path("api/v1/", include("apps.audit.urls")),
    path("api/v1/", include("apps.catalog.urls")),
    path("api/v1/instructor/", include("apps.content.urls")),
    path("api/v1/", include("apps.learning.urls")),
    path("api/v1/", include("apps.live_sessions.urls")),
    path("api/v1/", include("apps.assessments.urls")),
    path("api/v1/", include("apps.commerce.urls")),
    path("api/v1/", include("apps.billing.urls")),
    path("api/v1/", include("apps.payouts.urls")),
    path("api/v1/", include("apps.affiliates.urls")),
    path("api/v1/", include("apps.messaging.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.reviews.urls")),
    path("api/v1/", include("apps.support.urls")),
    path("api/v1/", include("apps.ai.urls")),
    path("api/v1/", include("apps.recommendations.urls")),
    path("api/v1/", include("apps.moderation.urls")),
    path("api/v1/", include("apps.platform_settings.urls")),
    path("api/v1/", include("apps.analytics.urls")),
    path("api/v1/", include("apps.privacy.urls")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]


def _serve_media_exempt(request, path, document_root=None):
    """
    Not django.conf.urls.static.static()'s default: PDF/video lesson content
    is displayed in an <iframe>/<video> from the Next.js dev origin
    (localhost:3000), a different origin than the API (localhost:8000). The
    global X_FRAME_OPTIONS = "DENY" baseline (see settings/base.py) would
    otherwise block the browser from framing these files, so this route
    alone is exempted from that header.

    Not using django.views.decorators.clickjacking.xframe_options_exempt
    directly on `serve`: that decorator only tags the response object
    `serve()` *returns*, but a missing file makes `serve()` raise Http404
    instead of returning — the decorator never runs, and the DENY header
    ends up back on the 404 page. Catching Http404 here and tagging the
    resulting 404 response too closes that gap.
    """
    try:
        response = serve(request, path, document_root=document_root)
    except Http404 as exc:
        response = page_not_found(request, exc)
    response.xframe_options_exempt = True
    return response


if settings.DEBUG:
    urlpatterns += [
        re_path(
            rf"^{settings.MEDIA_URL.lstrip('/')}(?P<path>.*)$",
            _serve_media_exempt,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
