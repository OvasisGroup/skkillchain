from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as SimpleJWTTokenRefreshView

from apps.audit.services import record_event

from .serializers import LogoutSerializer, MeSerializer, RegisterSerializer

User = get_user_model()


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


@extend_schema(tags=["Auth"])
class LoginView(TokenObtainPairView):
    # simplejwt's stub pins this to the literal empty-tuple type, not just
    # "a tuple" — too narrow to satisfy with any real value.
    permission_classes = (permissions.AllowAny,)  # type: ignore[assignment]
    throttle_scope = "auth-login"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            email = request.data.get(User.USERNAME_FIELD, "")
            user = User.objects.filter(email=User.objects.normalize_email(email)).first()
            record_event(
                actor=user,
                action="user.login",
                entity_type="User",
                entity_id=user.id if user else "",
                request=request,
            )
        return response


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
