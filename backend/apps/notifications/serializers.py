from rest_framework import serializers

from .models import EmailTemplate, Notification, NotificationTemplate


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "type", "channel", "title", "body", "read_at", "sent_at", "created_at"]


class MarkReadSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )


class MarkReadResultSerializer(serializers.Serializer):
    marked_read = serializers.IntegerField()


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            "id",
            "code",
            "channel",
            "locale",
            "subject_template",
            "body_template",
            "is_active",
        ]
        read_only_fields = ["id", "code", "channel", "locale"]


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = ["id", "code", "locale", "subject", "html_body", "text_body", "is_active"]
        read_only_fields = ["id", "code", "locale"]
