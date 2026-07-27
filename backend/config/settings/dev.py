from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True
SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-only-do-not-use-in-production")
ALLOWED_HOSTS = ["*"]

# Fixed dev-only Fernet key so `docker compose up` works with zero config.
# Never reuse this value anywhere real — see stage.py/prod.py.
FIELD_ENCRYPTION_KEY = env(
    "FIELD_ENCRYPTION_KEY", default="s3LWSgpk-Q63NAiMpe-gOvdOXqQVdlArhlraJKi8wn0="
)

# Local HTTP dev server has no TLS in front of it.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Next.js dev server's default port.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
