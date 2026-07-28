import os

from celery import Celery

# Same reasoning as config/wsgi.py: this is a container CMD in real
# deployments (worker/beat), so it fails safe to strict prod settings
# rather than a dev-friendly default. docker-compose sets
# DJANGO_SETTINGS_MODULE=config.settings.dev explicitly for local workers.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

app = Celery("skillchain")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
