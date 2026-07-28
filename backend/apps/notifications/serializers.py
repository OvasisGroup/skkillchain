from rest_framework import serializers

from .models import Notification


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
