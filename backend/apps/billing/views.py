from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event

from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer


@extend_schema(tags=["Payments"])
class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Plan.objects.filter(is_active=True)
    pagination_class = None


@extend_schema(tags=["Payments"])
class SubscriptionListView(generics.ListAPIView):
    """
    Subscriptions are created through checkout (an order with an
    item_type="plan" item), not a direct POST here — every paid resource
    goes through the same real payment flow (server-priced, provider-
    confirmed) rather than a second bypass path that skips payment
    entirely. This deliberately deviates from the earlier aspirational
    OpenAPI sketch's "POST /subscriptions" for that reason.
    """

    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Subscription.objects.filter(
            subscriber_type=Subscription.SUBSCRIBER_USER, subscriber_id=self.request.user.id
        ).select_related("plan")


@extend_schema(tags=["Payments"], request=None, responses={200: SubscriptionSerializer})
class SubscriptionCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id):
        subscription = get_object_or_404(Subscription, pk=id)
        if subscription.user_id != request.user.id:
            raise PermissionDenied("Not your subscription.")
        if subscription.status != Subscription.STATUS_ACTIVE:
            raise ValidationError(f"Cannot cancel a subscription that is '{subscription.status}'.")

        subscription.status = Subscription.STATUS_CANCELED
        subscription.canceled_at = timezone.now()
        subscription.save(update_fields=["status", "canceled_at"])
        record_event(
            actor=request.user,
            action="subscription.cancel",
            entity_type="Subscription",
            entity_id=subscription.id,
            request=request,
        )
        return Response(SubscriptionSerializer(subscription).data)
