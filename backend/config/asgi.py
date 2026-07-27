import os

from django.core.asgi import get_asgi_application

# See wsgi.py for why this defaults to prod. Channels routing for realtime
# features (messaging, notifications) is added in a later milestone
# (docs/07-delivery-planning/02-backend-build-milestones.md, M7) — for now
# this is a plain Django ASGI app.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_asgi_application()
