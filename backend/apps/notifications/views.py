from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
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


@extend_schema(
    tags=["Notifications"],
    description="Lists the current user's in-app notifications, most recent first.",
    examples=[
        OpenApiExample(
            "Notification",
            value={
                "id": "e5f6a7b8-...",
                "type": "course.approved",
                "channel": "in_app",
                "title": "Your course was approved",
                "body": '"Complete Python Bootcamp" is now published.',
                "read_at": None,
                "sent_at": "2026-02-01T12:00:00Z",
                "created_at": "2026-02-01T12:00:00Z",
            },
            response_only=True,
        )
    ],
)
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


@extend_schema(
    tags=["Notifications"],
    request=MarkReadSerializer,
    responses={200: MarkReadResultSerializer},
    description="Marks the current user's notifications as read — either the given IDs, or "
    "every unread notification if notification_ids is omitted.",
    examples=[
        OpenApiExample(
            "Mark specific notifications",
            value={"notification_ids": ["e5f6a7b8-5e6f-7a8b-9c0d-1e2f3a4b5c6d"]},
            request_only=True,
        ),
        OpenApiExample("Result", value={"marked_read": 1}, response_only=True),
    ],
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


@extend_schema(
    tags=["Admin"],
    description="Lists in-app/push notification templates across all channels and locales.",
    examples=[
        OpenApiExample(
            "Template",
            value={
                "id": "f6a7b8c9-...",
                "code": "course.approved",
                "channel": "in_app",
                "locale": "en",
                "subject_template": "",
                "body_template": '"{{course_title}}" is now published.',
                "is_active": True,
            },
            response_only=True,
        )
    ],
)
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
        request=NotificationTemplateSerializer,
        responses={200: NotificationTemplateSerializer},
        parameters=[OpenApiParameter("locale", str, description="Locale to update, default 'en'.")],
        description="Updates a notification template's body/subject for a given "
        "code+locale (selected via the ?locale= query param, default 'en').",
        examples=[
            OpenApiExample(
                "Update body",
                value={"body_template": '"{{course_title}}" is now published!'},
                request_only=True,
            )
        ],
    )
    def patch(self, request, code):
        locale = request.query_params.get("locale", "en")
        template = get_object_or_404(NotificationTemplate, code=code, locale=locale)
        serializer = NotificationTemplateSerializer(template, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(
    tags=["Admin"],
    description="Lists transactional email templates across all locales.",
    examples=[
        OpenApiExample(
            "Template",
            value={
                "id": "a7b8c9d0-...",
                "code": "welcome",
                "locale": "en",
                "subject": "Welcome to SkillChain",
                "html_body": "<p>Welcome, {{first_name}}!</p>",
                "text_body": "Welcome, {{first_name}}!",
                "is_active": True,
            },
            response_only=True,
        )
    ],
)
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

    @extend_schema(
        request=EmailTemplateSerializer,
        responses={200: EmailTemplateSerializer},
        parameters=[OpenApiParameter("locale", str, description="Locale to update, default 'en'.")],
        description="Updates an email template's subject/body for a given code+locale "
        "(selected via the ?locale= query param, default 'en').",
        examples=[
            OpenApiExample(
                "Update subject",
                value={"subject": "Welcome aboard, SkillChain!"},
                request_only=True,
            )
        ],
    )
    def patch(self, request, code):
        locale = request.query_params.get("locale", "en")
        template = get_object_or_404(EmailTemplate, code=code, locale=locale)
        serializer = EmailTemplateSerializer(template, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
