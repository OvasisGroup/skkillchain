from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.exceptions import AuthenticationFailed, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as SimpleJWTTokenRefreshView

from apps.audit.services import record_event
from shared.crypto import decrypt, encrypt

from . import mfa as mfa_lib
from .models import MFAFactor, OAuthIdentity
from .oauth.base import OAuthVerificationError
from .oauth.registry import get_provider
from .serializers import (
    LogoutSerializer,
    MeSerializer,
    MFAEnrollResponseSerializer,
    MFALoginChallengeSerializer,
    MFALoginVerifySerializer,
    MFAStatusResponseSerializer,
    MFAVerifySerializer,
    OAuthTokenSerializer,
    RegisterSerializer,
    TokenPairSerializer,
)

User = get_user_model()


def _token_pair_response(user) -> Response:
    refresh = RefreshToken.for_user(user)
    # simplejwt's stub types for_user()'s return as the base Token class,
    # which doesn't declare access_token — it's real on RefreshToken itself.
    access = refresh.access_token  # type: ignore[attr-defined]
    return Response({"access": str(access), "refresh": str(refresh)})


def _user_has_confirmed_mfa(user) -> bool:
    return MFAFactor.objects.filter(user=user, confirmed_at__isnull=False).exists()


@extend_schema(tags=["Auth"])
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        record_event(
            actor=user,
            action="user.register",
            entity_type="User",
            entity_id=user.id,
            request=request,
        )
        return Response(MeSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Auth"], responses={200: TokenPairSerializer, 202: MFALoginChallengeSerializer}
)
class LoginView(TokenObtainPairView):
    # simplejwt's stub pins this to the literal empty-tuple type, not just
    # "a tuple" — too narrow to satisfy with any real value.
    permission_classes = (permissions.AllowAny,)  # type: ignore[assignment]
    throttle_scope = "auth-login"

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user

        if _user_has_confirmed_mfa(user):
            challenge_token = mfa_lib.issue_login_challenge_token(user)
            record_event(
                actor=user,
                action="user.mfa_challenge_issued",
                entity_type="User",
                entity_id=user.id,
                request=request,
            )
            return Response(
                {"mfa_required": True, "mfa_token": challenge_token},
                status=status.HTTP_202_ACCEPTED,
            )

        record_event(
            actor=user, action="user.login", entity_type="User", entity_id=user.id, request=request
        )
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@extend_schema(tags=["Auth"])
class TokenRefreshView(SimpleJWTTokenRefreshView):
    pass


@extend_schema(tags=["Auth"], request=LogoutSerializer, responses={204: None})
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"detail": "refresh token required"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "invalid or already-used token"}, status=status.HTTP_400_BAD_REQUEST
            )

        record_event(
            actor=request.user,
            action="user.logout",
            entity_type="User",
            entity_id=request.user.id,
            request=request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Auth"])
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(tags=["Auth"], request=OAuthTokenSerializer, responses={200: TokenPairSerializer})
class OAuthLoginView(APIView):
    """
    Verifies a provider-issued token (the client does the OAuth dance with
    the provider's own SDK — Google Sign-In, Sign in with Apple, Facebook
    Login — and sends us the resulting token) rather than driving a
    server-side redirect flow, since this platform serves both a web and a
    native mobile client and this pattern is uniform across both.
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth-login"

    def post(self, request, provider):
        provider_adapter = get_provider(provider)
        if provider_adapter is None:
            raise NotFound(f"Unknown OAuth provider '{provider}'")

        serializer = OAuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            info = provider_adapter.verify(serializer.validated_data["token"])
        except OAuthVerificationError as exc:
            raise AuthenticationFailed(str(exc)) from exc

        identity = (
            OAuthIdentity.objects.select_related("user")
            .filter(provider=provider, provider_user_id=info.provider_user_id)
            .first()
        )

        created = False
        if identity is not None:
            user = identity.user
        else:
            user = None
            if info.email:
                existing = User.objects.filter(email=info.email).first()
                if existing is not None:
                    if not info.email_verified:
                        raise AuthenticationFailed(
                            "An account with this email already exists and the provider has not "
                            "verified it — log in with your password instead."
                        )
                    user = existing
            if user is None:
                if not info.email:
                    raise AuthenticationFailed("The provider did not return an email address")
                user = User.objects.create_user(email=info.email, password=None)
                created = True
            OAuthIdentity.objects.create(
                user=user,
                provider=provider,
                provider_user_id=info.provider_user_id,
                metadata={"email_verified": info.email_verified},
            )

        record_event(
            actor=user,
            action="user.oauth_register" if created else "user.oauth_login",
            entity_type="User",
            entity_id=user.id,
            request=request,
            payload={"provider": provider},
        )
        return _token_pair_response(user)


@extend_schema(tags=["Auth"], request=None, responses={201: MFAEnrollResponseSerializer})
class MFAEnrollView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Only ever one pending (unconfirmed) enrollment at a time — starting
        # over discards whatever was in progress.
        MFAFactor.objects.filter(user=request.user, confirmed_at__isnull=True).delete()

        secret = mfa_lib.generate_secret()
        factor = MFAFactor.objects.create(user=request.user, secret_encrypted=encrypt(secret))
        record_event(
            actor=request.user,
            action="mfa.enroll_started",
            entity_type="MFAFactor",
            entity_id=factor.id,
            request=request,
        )
        uri = mfa_lib.provisioning_uri(secret, request.user.email)
        return Response({"provisioning_uri": uri, "secret": secret}, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Auth"], request=MFAVerifySerializer, responses={200: MFAStatusResponseSerializer}
)
class MFAVerifyView(APIView):
    """Confirms a factor enrolled via /auth/mfa/enroll. For completing an
    MFA-gated login, see POST /auth/mfa/login-verify instead — that one
    doesn't require an existing session, since proving the second factor
    *is* how the session gets established."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "auth-mfa"

    def post(self, request):
        serializer = MFAVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        factor = (
            MFAFactor.objects.filter(user=request.user, confirmed_at__isnull=True)
            .order_by("-created_at")
            .first()
        )
        if factor is None:
            raise NotFound("No pending MFA enrollment to verify. Call /auth/mfa/enroll first.")

        if not mfa_lib.verify_code(
            decrypt(factor.secret_encrypted), serializer.validated_data["code"]
        ):
            record_event(
                actor=request.user,
                action="mfa.verify_failed",
                entity_type="MFAFactor",
                entity_id=factor.id,
                request=request,
            )
            raise AuthenticationFailed("Invalid code")

        factor.confirmed_at = timezone.now()
        factor.save(update_fields=["confirmed_at", "updated_at"])
        record_event(
            actor=request.user,
            action="mfa.enroll_confirmed",
            entity_type="MFAFactor",
            entity_id=factor.id,
            request=request,
        )
        return Response({"status": "confirmed"})


@extend_schema(
    tags=["Auth"], request=MFALoginVerifySerializer, responses={200: TokenPairSerializer}
)
class MFALoginVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth-mfa"

    def post(self, request):
        serializer = MFALoginVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = mfa_lib.resolve_login_challenge_token(serializer.validated_data["mfa_token"])
        user = User.objects.filter(id=user_id, is_active=True).first() if user_id else None
        if user is None:
            raise AuthenticationFailed("MFA challenge expired or invalid — log in again")

        factor = (
            MFAFactor.objects.filter(user=user, confirmed_at__isnull=False)
            .order_by("-created_at")
            .first()
        )
        if factor is None or not mfa_lib.verify_code(
            decrypt(factor.secret_encrypted), serializer.validated_data["code"]
        ):
            record_event(
                actor=user,
                action="mfa.login_verify_failed",
                entity_type="User",
                entity_id=user.id,
                request=request,
            )
            raise AuthenticationFailed("Invalid code")

        record_event(
            actor=user,
            action="user.login",
            entity_type="User",
            entity_id=user.id,
            request=request,
            payload={"mfa": True},
        )
        return _token_pair_response(user)
