"""
Settings shared by every environment.

SECRET_KEY, DEBUG, and ALLOWED_HOSTS are deliberately NOT set here — each of
dev.py / stage.py / prod.py sets them with the strictness appropriate to that
environment (dev.py supplies a dev-only fallback secret; stage/prod require a
real one from the environment and fail loudly if it's missing).
"""

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

# "daphne" must be first — it patches `runserver` to serve ASGI (incl.
# WebSockets) in dev; without it runserver stays plain-WSGI even with
# "channels" installed. See docs/07-delivery-planning/02-backend-build-
# milestones.md M7 and config/asgi.py.
INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
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
    "apps.live_sessions",
    "apps.assessments",
    "apps.billing",
    "apps.commerce",
    "apps.payouts",
    "apps.affiliates",
    "apps.messaging",
    "apps.notifications",
    "apps.reviews",
    "apps.support",
    "apps.ai",
    "apps.recommendations",
    "apps.moderation",
    "apps.platform_settings",
    "apps.analytics",
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

# Channels (M7 realtime — messaging/notifications/discussions): reuses the
# same Redis instance as the cache and Celery result backend above, no new
# infra. This is the layer group_send()/group_add() calls travel over, so
# it must be reachable from both the ASGI process and any Celery worker
# that pushes a live notification.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [env("REDIS_URL")]},
    }
}

# Celery: RabbitMQ as the broker, Redis for results (docs/01-architecture
# §Core Backend Components — "Async Processing"). Workers are a separate
# container/CMD (see infra/docker/docker-compose.yml worker/beat services),
# never invoked in-process from a web request.
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# Belt-and-suspenders alongside each task's own time_limit kwarg: nothing
# should be able to wedge a worker indefinitely.
CELERY_TASK_TIME_LIMIT = 300

CELERY_BEAT_SCHEDULE = {
    "live-sessions-dispatch-reminders": {
        "task": "live_sessions.dispatch_reminders",
        "schedule": 300.0,  # every 5 minutes
    },
    "live-sessions-poll-google-meet-recordings": {
        "task": "live_sessions.poll_google_meet_recordings",
        "schedule": 900.0,  # every 15 minutes
    },
    "live-sessions-close-ended-sessions": {
        "task": "live_sessions.close_ended_sessions",
        "schedule": 300.0,  # every 5 minutes
    },
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
        # Per-user/day caps on AI endpoints (M8 security checklist — bound
        # cost exposure on calls that hit a real, metered LLM API).
        "ai-chat": "60/day",
        "ai-generation": "20/day",
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
        "QuestionTypeEnum": "apps.assessments.models.Question.TYPE_CHOICES",
        "GradeEntryTypeEnum": "apps.assessments.serializers.GRADE_ENTRY_TYPE_CHOICES",
        "PaymentProviderEnum": "apps.commerce.serializers.PAYMENT_PROVIDER_CHOICES",
        "ConferencingProviderEnum": "apps.live_sessions.models.ConferencingAccount.PROVIDER_CHOICES",
        "SupportTicketStatusEnum": "apps.support.models.SupportTicket.STATUS_CHOICES",
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

# Conferencing OAuth (live sessions) — full authorization-code flow per
# instructor. See apps/live_sessions/conferencing/ and
# docs/01-architecture/01-technical-architecture.md §3.1 for why this is a
# separate credential set from GOOGLE_OAUTH_CLIENT_ID above.
ZOOM_CLIENT_ID = env("ZOOM_CLIENT_ID", default="")
ZOOM_CLIENT_SECRET = env("ZOOM_CLIENT_SECRET", default="")
ZOOM_REDIRECT_URI = env("ZOOM_REDIRECT_URI", default="")
GOOGLE_MEET_CLIENT_ID = env("GOOGLE_MEET_CLIENT_ID", default="")
GOOGLE_MEET_CLIENT_SECRET = env("GOOGLE_MEET_CLIENT_SECRET", default="")
GOOGLE_MEET_REDIRECT_URI = env("GOOGLE_MEET_REDIRECT_URI", default="")

# Payment provider credentials (M6 commerce) — see apps/commerce/providers/
# for the adapter behind each. All default to "" in dev; anything that
# actually calls out to a real provider simply fails with a clear
# PaymentProviderError until real credentials are supplied.
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
PAYPAL_CLIENT_ID = env("PAYPAL_CLIENT_ID", default="")
PAYPAL_CLIENT_SECRET = env("PAYPAL_CLIENT_SECRET", default="")
PAYPAL_WEBHOOK_ID = env("PAYPAL_WEBHOOK_ID", default="")
FLUTTERWAVE_SECRET_KEY = env("FLUTTERWAVE_SECRET_KEY", default="")
FLUTTERWAVE_WEBHOOK_SECRET_HASH = env("FLUTTERWAVE_WEBHOOK_SECRET_HASH", default="")
PAYSTACK_SECRET_KEY = env("PAYSTACK_SECRET_KEY", default="")
MPESA_CONSUMER_KEY = env("MPESA_CONSUMER_KEY", default="")
MPESA_CONSUMER_SECRET = env("MPESA_CONSUMER_SECRET", default="")
MPESA_SHORTCODE = env("MPESA_SHORTCODE", default="")
MPESA_PASSKEY = env("MPESA_PASSKEY", default="")
# M-Pesa callbacks carry no signature (see providers/mpesa.py docstring) —
# this secret path segment is the practical substitute for local
# verification; real IP allowlisting still belongs at the infra layer.
MPESA_CALLBACK_SECRET = env("MPESA_CALLBACK_SECRET", default="")
MPESA_CALLBACK_URL = env("MPESA_CALLBACK_URL", default="")

# Instructor revenue share (M6 payouts) — instructor keeps
# (1 - PLATFORM_COMMISSION_RATE) of each course sale, credited to their
# wallet at payment-success time. No documented source of truth for the
# real rate exists yet (no pricing/finance doc specifies one), so this is
# a reasonable default (Udemy-style ~70/30 split) rather than a value
# taken from product requirements — flagged here for finance sign-off.
PLATFORM_COMMISSION_RATE = Decimal(env("PLATFORM_COMMISSION_RATE", default="0.30"))

# Affiliate referral commission — percent of the referred order's
# total_amount, credited to the affiliate's wallet on payment success.
# Same "no documented source of truth" caveat as PLATFORM_COMMISSION_RATE.
AFFILIATE_DEFAULT_COMMISSION_RATE = Decimal(env("AFFILIATE_DEFAULT_COMMISSION_RATE", default="10.00"))

# Outbound email (M7 notifications) — console backend by default so dev/
# test never accidentally sends real mail; stage/prod override EMAIL_BACKEND
# to an SMTP backend via env once real credentials exist. See
# apps/notifications/providers/email.py.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@skillchain.example")

# SMS/push notification channels (M7): no vendor is named anywhere in the
# SRS/product docs (unlike Stripe/PayPal/etc. for payments, which each have
# a documented required integration). apps/notifications/providers/sms.py
# and push.py are real adapter interfaces with a log-only implementation
# behind them, pending an actual vendor decision (e.g. Twilio, FCM) — same
# "identify but don't fake a send" precedent as
# apps/live_sessions/tasks.py's dispatch_reminders before this milestone.

# AI-assisted learning (M8) — real Anthropic Claude integration, unlike the
# SMS/push stubs above, per an explicit choice to wire a real LLM rather
# than a stub. Sonnet, not Opus: this is a cost-metered production feature
# with per-user/day rate limits (see DEFAULT_THROTTLE_RATES above), not a
# one-off hard-reasoning task — Sonnet is the documented high-volume
# production pick. Empty default means calling out fails loudly with a
# clear AIProviderError (apps/ai/anthropic_client.py) rather than a silent
# no-op, same "safe default, override via env" pattern as STRIPE_SECRET_KEY.
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")
AI_CHAT_MODEL = env("AI_CHAT_MODEL", default="claude-sonnet-5")
AI_GENERATION_MODEL = env("AI_GENERATION_MODEL", default="claude-sonnet-5")
