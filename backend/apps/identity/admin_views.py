from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.authorization.permissions import HasPermission

from .admin_serializers import AdminUserSerializer, AdminUserStatusUpdateSerializer
from .models import User


@extend_schema(tags=["Admin"])
class AdminUserListView(generics.ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [HasPermission]
    required_permission = "users.manage"

    def get_queryset(self):
        queryset = User.objects.all()
        email = self.request.query_params.get("email")
        if email:
            queryset = queryset.filter(email__icontains=email)
        return queryset


@extend_schema(
    tags=["Admin"], request=AdminUserStatusUpdateSerializer, responses={200: AdminUserSerializer}
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
