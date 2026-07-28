from rest_framework import serializers

from .models import SupportTicket, SupportTicketMessage


class SupportTicketSerializer(serializers.ModelSerializer):
    is_sla_breached = serializers.BooleanField(read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "requester",
            "assignee",
            "category",
            "priority",
            "status",
            "subject",
            "is_sla_breached",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["requester", "assignee", "status"]


class SupportTicketCreateSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=SupportTicket.CATEGORY_CHOICES)
    priority = serializers.ChoiceField(
        choices=SupportTicket.PRIORITY_CHOICES, default=SupportTicket.PRIORITY_NORMAL
    )
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField(allow_blank=False)


class SupportTicketMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicketMessage
        fields = ["id", "ticket", "sender", "body", "created_at"]


class SupportTicketMessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(allow_blank=False)
