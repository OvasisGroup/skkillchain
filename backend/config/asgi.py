import os

from django.core.asgi import get_asgi_application

# Same reasoning as wsgi.py: this is a container CMD in real deployments, so
# it fails safe to strict prod settings rather than a dev-friendly default.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

# get_asgi_application() runs django.setup() — app registry must be ready
# before anything below imports models (via consumers/routing), so this
# call has to come before those imports, not after.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from apps.messaging.routing import websocket_urlpatterns as messaging_ws_urlpatterns  # noqa: E402
from shared.channels_auth import JWTAuthMiddlewareStack  # noqa: E402

# apps.notifications.routing / apps.reviews.routing are added here as each
# of those M7 slices lands (see docs/07-delivery-planning/
# 02-backend-build-milestones.md) — combined the same way
# messaging_ws_urlpatterns is below.
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddlewareStack(URLRouter(messaging_ws_urlpatterns)),
    }
)
