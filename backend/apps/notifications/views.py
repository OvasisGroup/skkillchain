from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authorization.permissions import HasPermission

from .models import EmailTemplate, Notification, NotificationTemplate
from .serializers import (
    EmailTemplateSerializer,
    MarkReadResultSerializer,
    MarkReadSerializer,
    NotificationSerializer,
    NotificationTemplateSerializer,
)


@extend_schema(tags=["Notifications"])
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


@extend_schema(
    tags=["Notifications"], request=MarkReadSerializer, responses={200: MarkReadResultSerializer}
)
class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data.get("notification_ids")

        queryset = Notification.objects.filter(user=request.user, read_at__isnull=True)
        if ids:
            queryset = queryset.filter(id__in=ids)
        marked_read = queryset.update(read_at=timezone.now())

        return Response({"marked_read": marked_read})


@extend_schema(tags=["Admin"])
class AdminNotificationTemplateListView(generics.ListAPIView):
    serializer_class = NotificationTemplateSerializer
    permission_classes = [HasPermission]
    required_permission = "templates.manage"
    queryset = NotificationTemplate.objects.all()
    pagination_class = None


@extend_schema(tags=["Admin"])
class AdminNotificationTemplateUpdateView(APIView):
    permission_classes = [HasPermission]
    required_permission = "templates.manage"
    throttle_scope = "admin-write"

    @extend_schema(
        request=NotificationTemplateSerializer, responses={200: NotificationTemplateSerializer}
    )
    def patch(self, request, code):
        locale = request.query_params.get("locale", "en")
        template = get_object_or_404(NotificationTemplate, code=code, locale=locale)
        serializer = NotificationTemplateSerializer(template, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(tags=["Admin"])
class AdminEmailTemplateListView(generics.ListAPIView):
    serializer_class = EmailTemplateSerializer
    permission_classes = [HasPermission]
    required_permission = "templates.manage"
    queryset = EmailTemplate.objects.all()
    pagination_class = None


@extend_schema(tags=["Admin"])
class AdminEmailTemplateUpdateView(APIView):
    permission_classes = [HasPermission]
    required_permission = "templates.manage"
    throttle_scope = "admin-write"

    @extend_schema(request=EmailTemplateSerializer, responses={200: EmailTemplateSerializer})
    def patch(self, request, code):
        locale = request.query_params.get("locale", "en")
        template = get_object_or_404(EmailTemplate, code=code, locale=locale)
        serializer = EmailTemplateSerializer(template, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
