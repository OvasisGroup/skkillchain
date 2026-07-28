from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import MarkReadResultSerializer, MarkReadSerializer, NotificationSerializer


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
