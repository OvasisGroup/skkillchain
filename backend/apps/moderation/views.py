from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.authorization.permissions import HasPermission
from shared.api.pagination import AppliedAtCursorPagination

from . import services
from .models import InstructorApplication
from .serializers import InstructorApplicationSerializer


@extend_schema(tags=["Instructor"], request=None, responses={200: InstructorApplicationSerializer})
class InstructorApplyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        application = services.apply_as_instructor(request.user)
        record_event(
            actor=request.user,
            action="instructor_application.create",
            entity_type="InstructorApplication",
            entity_id=application.id,
            request=request,
        )
        return Response(InstructorApplicationSerializer(application).data, status=201)


@extend_schema(tags=["Admin"])
class AdminInstructorListView(generics.ListAPIView):
    serializer_class = InstructorApplicationSerializer
    permission_classes = [HasPermission]
    required_permission = "instructors.approve"
    pagination_class = AppliedAtCursorPagination

    def get_queryset(self):
        queryset = InstructorApplication.objects.select_related("user")
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


@extend_schema(tags=["Admin"], request=None, responses={200: InstructorApplicationSerializer})
class AdminInstructorApproveView(APIView):
    permission_classes = [HasPermission]
    required_permission = "instructors.approve"
    throttle_scope = "admin-write"

    def post(self, request, user_id):
        application = services.approve_instructor_application(user_id, request.user)
        record_event(
            actor=request.user,
            action="instructor_application.approve",
            entity_type="InstructorApplication",
            entity_id=application.id,
            request=request,
        )
        return Response(InstructorApplicationSerializer(application).data)
