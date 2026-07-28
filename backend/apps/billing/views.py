from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event

from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer

_PLAN_EXAMPLE = {
    "id": "f9a0b1c2-...",
    "code": "pro-monthly",
    "name": "Pro Monthly",
    "billing_interval": "monthly",
    "price_amount": "19.99",
    "currency": "USD",
    "seat_model": "individual",
    "features_json": {"max_courses": None, "offline_download": True},
}


@extend_schema(
    tags=["Payments"],
    description="Lists active subscription plans available for purchase.",
    examples=[OpenApiExample("Plan", value=_PLAN_EXAMPLE, response_only=True)],
)
class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Plan.objects.filter(is_active=True)
    pagination_class = None


@extend_schema(
    tags=["Payments"],
    description="Lists the current user's subscriptions. Subscriptions are created through "
    "checkout (an order with an item_type=plan item), not a direct create endpoint here — "
    "every paid resource goes through the same server-priced, provider-confirmed payment flow.",
    examples=[
        OpenApiExample(
            "Subscription",
            value={
                "id": "a0b1c2d3-...",
                "plan": _PLAN_EXAMPLE,
                "status": "active",
                "started_at": "2026-01-01T00:00:00Z",
                "renews_at": "2026-03-01T00:00:00Z",
                "canceled_at": None,
            },
            response_only=True,
        )
    ],
)
class SubscriptionListView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Subscription.objects.filter(
            subscriber_type=Subscription.SUBSCRIBER_USER, subscriber_id=self.request.user.id
        ).select_related("plan")


@extend_schema(
    tags=["Payments"],
    request=None,
    responses={200: SubscriptionSerializer},
    description="Cancels one of the current user's own active subscriptions. Fails with 400 "
    "if it isn't currently active.",
    examples=[
        OpenApiExample(
            "Canceled",
            value={
                "id": "a0b1c2d3-...",
                "plan": _PLAN_EXAMPLE,
                "status": "canceled",
                "started_at": "2026-01-01T00:00:00Z",
                "renews_at": "2026-03-01T00:00:00Z",
                "canceled_at": "2026-02-10T09:00:00Z",
            },
            response_only=True,
        )
    ],
)
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
