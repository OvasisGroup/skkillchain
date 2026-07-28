"""
Settings shared by every environment.

SECRET_KEY, DEBUG, and ALLOWED_HOSTS are deliberately NOT set here — each of
dev.py / stage.py / prod.py sets them with the strictness appropriate to that
environment (dev.py supplies a dev-only fallback secret; stage/prod require a
real one from the environment and fail loudly if it's missing).
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "apps.identity",
    "apps.authorization",
    "apps.audit",
    "apps.catalog",
    "apps.content",
    "apps.learning",
    "shared.health",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

AUTH_USER_MODEL = "identity.User"

# Argon2 first (OWASP-recommended); PBKDF2 kept so any pre-existing hashes
# using Django's old default remain verifiable.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        # Stronger than Django's default of 8, matching the security posture in
        # docs/06-devops-security-qa/02-security-test-qa.md.
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Security baseline that holds in every environment. Cookie/SSL enforcement is
# environment-specific (see dev.py vs stage.py/prod.py) since it must be
# relaxed for local HTTP development.
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_REFERRER_POLICY = "same-origin"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # Deny-by-default: every new endpoint requires an explicit permission_classes
    # override to be reachable by anyone other than an authenticated user.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "shared.api.exceptions.rfc7807_exception_handler",
    # Cursor-based per docs/03-api/01-api-documentation.md §1 — stable under
    # concurrent writes to the underlying list, unlike offset pagination.
    "DEFAULT_PAGINATION_CLASS": "shared.api.pagination.DefaultCursorPagination",
    "PAGE_SIZE": 20,
    # Opt-in per-view via `throttle_scope = "..."` — a no-op for views that
    # don't set one, so this is safe as a global default.
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "auth-login": "10/min",
        "auth-mfa": "10/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    # Reuse detection: rotating a refresh token blacklists the old one, so a
    # stolen-and-replayed refresh token fails once the legitimate client
    # rotates first (see docs/06-devops-security-qa/02-security-test-qa.md).
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SkillChain Learning Platform API",
    "DESCRIPTION": "Enterprise learning platform REST API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Course.status and Enrollment.status are both named "status" with
    # different choice sets; drf-spectacular auto-resolves the collision
    # with a hash-suffixed name (e.g. "Status009Enum") but still emits a
    # warning for it, which --fail-on-warn (CI) treats as fatal. Naming
    # both explicitly is the actual fix, not just quieting the warning.
    "ENUM_NAME_OVERRIDES": {
        "CourseStatusEnum": "apps.catalog.models.Course.STATUS_CHOICES",
        "EnrollmentStatusEnum": "apps.learning.models.Enrollment.STATUS_CHOICES",
    },
}

# FIELD_ENCRYPTION_KEY is deliberately NOT set here, same reasoning as
# SECRET_KEY at the top of this file — see dev.py / stage.py / prod.py.

# OAuth2 social login client IDs (used as the expected `aud` claim when
# verifying provider tokens — see apps/identity/oauth/).
GOOGLE_OAUTH_CLIENT_ID = env("GOOGLE_OAUTH_CLIENT_ID", default="")
APPLE_OAUTH_CLIENT_ID = env("APPLE_OAUTH_CLIENT_ID", default="")

# Web frontend origin — used to build user-facing links (e.g. a
# certificate's QR verification URL) that point at the app, not the API.
PUBLIC_APP_URL = env("PUBLIC_APP_URL", default="http://localhost:3000")
