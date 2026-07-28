from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _user_from_access_token(raw_token: str):
    try:
        # simplejwt's own type stub annotates `token` as `Optional["Token"]`,
        # but its runtime contract (see tokens.py's __init__ docstring/body)
        # is that this is the raw encoded string — a stub inaccuracy, not a
        # real type error here.
        validated = AccessToken(raw_token)  # type: ignore[arg-type]
    except TokenError:
        return AnonymousUser()
    User = get_user_model()
    user_id: str = validated[settings.SIMPLE_JWT["USER_ID_CLAIM"]]  # type: ignore[index]
    try:
        return User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    WebSocket connections authenticate with the same JWT access token the
    REST API uses (rest_framework_simplejwt) — passed as a `?token=`
    query-string param since a browser can't set an Authorization header
    on the WS handshake. Validation mirrors what JWTAuthentication does
    internally for REST requests (SIMPLE_JWT["USER_ID_CLAIM"] -> user
    lookup). An invalid/missing/expired token just leaves scope["user"]
    anonymous — it's each consumer's job to reject an unauthenticated
    connection, same as `permission_classes` does for a REST view.
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]
        scope["user"] = await _user_from_access_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
