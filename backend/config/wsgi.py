import os

from django.core.wsgi import get_wsgi_application

# Defaults to prod so a misconfigured deployment fails safe (strict settings)
# rather than accidentally booting with DEBUG on. Local/dev entrypoints
# (manage.py, docker-compose) set DJANGO_SETTINGS_MODULE explicitly.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
