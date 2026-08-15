from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.authorization.permissions import HasPermission

from .admin_serializers import AdminUserSerializer, AdminUserStatusUpdateSerializer
from .models import User

_ADMIN_USER_EXAMPLE = {
    "id": "b6a5b6c0-9b1e-4c9a-9b7a-1f2e3d4c5b6a",
    "email": "student@example.com",
    "is_active": True,
    "created_at": "2026-01-15T09:00:00Z",
}


@extend_schema(
    tags=["Admin"],
    parameters=[
        OpenApiParameter("email", str, description="Case-insensitive substring filter on email."),
        OpenApiParameter(
            "role", str, description="Filter to users holding this role code, e.g. 'instructor'."
        ),
    ],
    description="Lists platform users, optionally filtered by an email substring and/or role.",
    examples=[OpenApiExample("User", value=_ADMIN_USER_EXAMPLE, response_only=True)],
)
class AdminUserListView(generics.ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [HasPermission]
    required_permission = "users.manage"

    def get_queryset(self):
        queryset = User.objects.all()
        email = self.request.query_params.get("email")
        if email:
            queryset = queryset.filter(email__icontains=email)
        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(user_roles__role__code=role).distinct()
        return queryset


@extend_schema(
    tags=["Admin"],
    request=AdminUserStatusUpdateSerializer,
    responses={200: AdminUserSerializer},
    description="Suspends or reinstates a user account by toggling is_active.",
    examples=[
        OpenApiExample("Suspend", value={"is_active": False}, request_only=True),
        OpenApiExample(
            "Suspended",
            value={**_ADMIN_USER_EXAMPLE, "is_active": False},
            response_only=True,
        ),
    ],
)
class AdminUserStatusUpdateView(APIView):
    permission_classes = [HasPermission]
    required_permission = "users.manage"
    throttle_scope = "admin-write"

    def patch(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        serializer = AdminUserStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_active = serializer.validated_data["is_active"]

        user.is_active = is_active
        user.save(update_fields=["is_active"])
        record_event(
            actor=request.user,
            action="user.reinstate" if is_active else "user.suspend",
            entity_type="User",
            entity_id=user.id,
            request=request,
        )
        return Response(AdminUserSerializer(user).data)
