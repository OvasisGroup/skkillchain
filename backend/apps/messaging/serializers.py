from rest_framework import serializers

from .models import Message, Thread


class ThreadSerializer(serializers.ModelSerializer):
    participant_ids = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = ["id", "thread_type", "subject", "created_by", "created_at", "participant_ids"]

    def get_participant_ids(self, thread):
        return [str(user_id) for user_id in thread.participants.values_list("user_id", flat=True)]


class ThreadCreateSerializer(serializers.Serializer):
    thread_type = serializers.ChoiceField(
        choices=Thread.THREAD_TYPE_CHOICES, default=Thread.TYPE_DIRECT
    )
    subject = serializers.CharField(required=False, allow_blank=True, default="")
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=False
    )


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "thread", "sender", "body", "metadata", "created_at"]


class MessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(allow_blank=False)
