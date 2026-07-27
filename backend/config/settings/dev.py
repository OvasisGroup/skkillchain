from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True
SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-only-do-not-use-in-production")
ALLOWED_HOSTS = ["*"]

# Local HTTP dev server has no TLS in front of it.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
