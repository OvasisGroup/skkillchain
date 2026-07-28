from django.contrib import admin
from django.urls import include, path
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
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
