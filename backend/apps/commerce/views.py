from decimal import Decimal

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.authorization.permissions import HasPermission
from apps.catalog.models import Course

from . import services
from .models import Coupon, GiftCard, Invoice, Order, Payment, Promotion, Refund, WebhookEvent
from .providers.base import PaymentProviderError, WebhookVerificationError
from .providers.registry import get_provider
from .serializers import (
    ApplyCouponSerializer,
    ApplyGiftCardSerializer,
    CouponSerializer,
    GiftCardBalanceSerializer,
    InvoiceSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    PaymentSerializer,
    PayResponseSerializer,
    PaySerializer,
    PromotionSerializer,
    RefundCreateSerializer,
    RefundSerializer,
)


def _owned_order_or_404(order_id, user):
    return get_object_or_404(Order, pk=order_id, buyer=user)


def _owned_course_or_403(course_id, user):
    course = get_object_or_404(Course, pk=course_id)
    if course.owner_id != user.id:
        raise PermissionDenied("You do not own this course.")
    return course


# ---------- Checkout ----------

_ORDER_EXAMPLE = {
    "id": "e1f2a3b4-...",
    "status": "pending",
    "subtotal_amount": "49.99",
    "discount_amount": "0.00",
    "tax_amount": "0.00",
    "gift_card_amount": "0.00",
    "total_amount": "49.99",
    "currency": "USD",
    "items": [
        {
            "id": "f2a3b4c5-...",
            "item_type": "course",
            "item_id": "1c2d3e4f-...",
            "unit_price": "49.99",
            "quantity": 1,
        }
    ],
    "created_at": "2026-02-01T12:00:00Z",
}


@extend_schema(
    tags=["Payments"],
    request=OrderCreateSerializer,
    responses={201: OrderSerializer},
    description="Creates a pending order from one or more cart items (courses or "
    "subscription plans). Prices are computed server-side from the current catalog/plan "
    "prices, never trusted from the client.",
    examples=[
        OpenApiExample(
            "Create order",
            value={
                "items": [
                    {"item_type": "course", "item_id": "1c2d3e4f-5a6b-7c8d-9e0f-1a2b3c4d5e6f"}
                ]
            },
            request_only=True,
        ),
        OpenApiExample("Order created", value=_ORDER_EXAMPLE, response_only=True),
    ],
)
class CheckoutOrderCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "financial-write"

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        priced_items = services.price_items(serializer.validated_data["items"])

        order = Order.objects.create(buyer=request.user, currency=priced_items[0]["currency"])
        for item in priced_items:
            order.items.create(
                item_type=item["item_type"],
                item_id=item["item_id"],
                unit_price=item["unit_price"],
                quantity=item["quantity"],
            )
        services.compute_order_totals(order)
        referral_code = serializer.validated_data.get("referral_code", "")
        if referral_code:
            services.capture_referral(order, referral_code, request.user)
        record_event(
            actor=request.user,
            action="order.create",
            entity_type="Order",
            entity_id=order.id,
            request=request,
        )
        return Response(OrderSerializer(order).data, status=201)


@extend_schema(
    tags=["Payments"],
    request=ApplyCouponSerializer,
    responses={200: OrderSerializer},
    description="Applies a coupon code to a pending order the current user owns, recomputing "
    "the discount/total. Fails with 400 if the order is no longer pending or the coupon is "
    "invalid/expired/exhausted.",
    examples=[
        OpenApiExample("Apply coupon", value={"code": "WELCOME10"}, request_only=True),
        OpenApiExample(
            "Discount applied",
            value={**_ORDER_EXAMPLE, "discount_amount": "5.00", "total_amount": "44.99"},
            response_only=True,
        ),
    ],
)
class ApplyCouponView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "financial-write"

    def post(self, request, order_id):
        order = _owned_order_or_404(order_id, request.user)
        if order.status != Order.STATUS_PENDING:
            raise ValidationError(f"Cannot modify an order that is '{order.status}'.")

        serializer = ApplyCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.apply_coupon(order, serializer.validated_data["code"], request.user)
        return Response(OrderSerializer(order).data)


@extend_schema(
    tags=["Payments"],
    request=ApplyGiftCardSerializer,
    responses={200: OrderSerializer},
    description="Applies a gift card balance (fully or the given amount) to a pending order "
    "the current user owns. The actual balance deduction only happens once payment succeeds.",
    examples=[
        OpenApiExample("Apply gift card", value={"code": "GIFT-ABC123"}, request_only=True),
        OpenApiExample(
            "Gift card applied",
            value={**_ORDER_EXAMPLE, "gift_card_amount": "20.00", "total_amount": "29.99"},
            response_only=True,
        ),
    ],
)
class ApplyGiftCardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "financial-write"

    def post(self, request, order_id):
        order = _owned_order_or_404(order_id, request.user)
        if order.status != Order.STATUS_PENDING:
            raise ValidationError(f"Cannot modify an order that is '{order.status}'.")

        serializer = ApplyGiftCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.apply_gift_card(
            order, serializer.validated_data["code"], serializer.validated_data.get("amount")
        )
        return Response(OrderSerializer(order).data)


@extend_schema(
    tags=["Payments"],
    request=PaySerializer,
    responses={200: PayResponseSerializer},
    description="Starts payment for a pending order via the given provider. If the order "
    "total is fully covered by coupons/gift cards, settles immediately with no provider call. "
    "Otherwise returns a client_secret and/or redirect_url for the client to complete payment; "
    "the order finalizes once the provider's webhook confirms success.",
    examples=[
        OpenApiExample("Pay with Stripe", value={"provider": "stripe"}, request_only=True),
        OpenApiExample(
            "Payment initiated",
            value={
                "payment": {
                    "id": "a4b5c6d7-...",
                    "order": "e1f2a3b4-...",
                    "provider": "stripe",
                    "provider_payment_id": "pi_1AbCdEfGhIjKlMnO",
                    "status": "pending",
                    "amount": "49.99",
                    "currency": "USD",
                    "paid_at": None,
                },
                "client_secret": "pi_1AbCdEfGhIjKlMnO_secret_xyz",
                "redirect_url": None,
            },
            response_only=True,
        ),
    ],
)
class PayOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "financial-write"

    def post(self, request, order_id):
        order = _owned_order_or_404(order_id, request.user)
        if order.status != Order.STATUS_PENDING:
            raise ValidationError(f"Cannot pay an order that is '{order.status}'.")

        serializer = PaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider_code = serializer.validated_data["provider"]

        # Fully covered by coupon/gift-card — never call a provider for
        # $0, and never let a client-submitted amount decide this either.
        if order.total_amount <= 0:
            payment = Payment.objects.create(
                order=order,
                provider=provider_code,
                status=Payment.STATUS_SUCCEEDED,
                amount=Decimal("0"),
                currency=order.currency,
                paid_at=timezone.now(),
            )
            services.finalize_order_payment(order)
            return Response(
                {
                    "payment": PaymentSerializer(payment).data,
                    "client_secret": None,
                    "redirect_url": None,
                }
            )

        provider_adapter = get_provider(provider_code)
        if provider_adapter is None:
            raise NotFound(f"Unknown payment provider '{provider_code}'")

        extra_kwargs = {}
        if provider_code == "mpesa":
            extra_kwargs["phone_number"] = serializer.validated_data.get("phone_number")

        try:
            init = provider_adapter.create_payment(
                amount=order.total_amount,
                currency=order.currency,
                order_id=str(order.id),
                **extra_kwargs,
            )
        except PaymentProviderError as exc:
            raise ValidationError(f"Could not start payment: {exc}") from exc

        payment = Payment.objects.create(
            order=order,
            provider=provider_code,
            provider_payment_id=init.provider_payment_id,
            status=Payment.STATUS_PENDING,
            amount=order.total_amount,
            currency=order.currency,
        )
        record_event(
            actor=request.user,
            action="payment.initiate",
            entity_type="Payment",
            entity_id=payment.id,
            request=request,
        )
        return Response(
            {
                "payment": PaymentSerializer(payment).data,
                "client_secret": init.client_secret,
                "redirect_url": init.redirect_url,
            }
        )


@extend_schema(
    tags=["Payments"],
    description="Lists payments (across all providers) for orders the current user placed.",
    examples=[
        OpenApiExample(
            "Payment",
            value={
                "id": "a4b5c6d7-...",
                "order": "e1f2a3b4-...",
                "provider": "stripe",
                "provider_payment_id": "pi_1AbCdEfGhIjKlMnO",
                "status": "succeeded",
                "amount": "49.99",
                "currency": "USD",
                "paid_at": "2026-02-01T12:05:00Z",
            },
            response_only=True,
        )
    ],
)
class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Payment.objects.filter(order__buyer=self.request.user).select_related("order")


@extend_schema(
    tags=["Payments"],
    description="Lists invoices for orders the current user placed.",
    examples=[
        OpenApiExample(
            "Invoice",
            value={
                "id": "b5c6d7e8-...",
                "order": "e1f2a3b4-...",
                "invoice_number": "INV-2026-00042",
                "tax_metadata": {},
                "issued_at": "2026-02-01T12:05:00Z",
            },
            response_only=True,
        )
    ],
)
class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Invoice.objects.filter(order__buyer=self.request.user).select_related("order")


@extend_schema(
    tags=["Payments"],
    request=RefundCreateSerializer,
    responses={201: RefundSerializer},
    description="Requests a refund (full or partial) for one of the current user's own "
    "succeeded payments, processed through the original payment provider.",
    examples=[
        OpenApiExample(
            "Request refund",
            value={
                "payment_id": "a4b5c6d7-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
                "amount": "49.99",
                "reason": "Course not as described",
            },
            request_only=True,
        ),
        OpenApiExample(
            "Refund",
            value={
                "id": "c6d7e8f9-...",
                "payment": "a4b5c6d7-...",
                "provider_refund_id": "re_1AbCdEfGhIjKlMnO",
                "amount": "49.99",
                "reason": "Course not as described",
                "status": "succeeded",
                "requested_at": "2026-02-05T10:00:00Z",
            },
            response_only=True,
        ),
    ],
)
class RefundCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "financial-write"

    def post(self, request):
        serializer = RefundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        payment = get_object_or_404(Payment, pk=data["payment_id"], order__buyer=request.user)
        if payment.status != Payment.STATUS_SUCCEEDED:
            raise ValidationError(f"Cannot refund a payment that is '{payment.status}'.")
        if data["amount"] > payment.amount:
            raise ValidationError("Refund amount cannot exceed the original payment amount.")

        provider_adapter = get_provider(payment.provider)
        if provider_adapter is None:
            raise NotFound(f"Unknown payment provider '{payment.provider}'")

        refund = Refund.objects.create(
            payment=payment, amount=data["amount"], reason=data.get("reason", "")
        )
        try:
            result = provider_adapter.refund_payment(
                payment.provider_payment_id, amount=data["amount"]
            )
        except PaymentProviderError as exc:
            refund.status = Refund.STATUS_FAILED
            refund.save(update_fields=["status"])
            raise ValidationError(f"Refund failed: {exc}") from exc

        refund.provider_refund_id = result.provider_refund_id
        refund.status = result.status
        refund.save(update_fields=["provider_refund_id", "status"])
        if result.status == "succeeded":
            payment.status = Payment.STATUS_REFUNDED
            payment.save(update_fields=["status"])
            payment.order.status = Order.STATUS_REFUNDED
            payment.order.save(update_fields=["status"])

        record_event(
            actor=request.user,
            action="refund.request",
            entity_type="Refund",
            entity_id=refund.id,
            request=request,
        )
        return Response(RefundSerializer(refund).data, status=201)


@extend_schema(
    tags=["Payments"],
    responses={200: GiftCardBalanceSerializer},
    description="Public lookup of a gift card's remaining balance by code.",
    examples=[
        OpenApiExample(
            "Gift card",
            value={
                "code": "GIFT-ABC123",
                "balance_amount": "20.00",
                "currency": "USD",
                "expires_at": None,
            },
            response_only=True,
        )
    ],
)
class GiftCardBalanceView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, code):
        gift_card = get_object_or_404(GiftCard, code=code)
        return Response(GiftCardBalanceSerializer(gift_card).data)


# ---------- Instructor / Admin coupon & promotion authoring ----------


_COUPON_EXAMPLE = {
    "id": "d7e8f9a0-...",
    "code": "SPRING25",
    "discount_type": "percentage",
    "discount_value": "25",
    "valid_from": "2026-03-01T00:00:00Z",
    "valid_to": "2026-03-31T23:59:59Z",
    "usage_limit": 100,
    "per_user_limit": 1,
    "promotion": None,
    "course": "1c2d3e4f-...",
}


@extend_schema(
    tags=["Instructor"],
    request=CouponSerializer,
    responses={201: CouponSerializer},
    description="Creates a coupon scoped to a single course the current instructor owns.",
    examples=[
        OpenApiExample("Create coupon", value=_COUPON_EXAMPLE, request_only=True),
        OpenApiExample("Created", value=_COUPON_EXAMPLE, response_only=True),
    ],
)
class InstructorCouponCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "financial-write"

    def post(self, request, course_id):
        course = _owned_course_or_403(course_id, request.user)
        serializer = CouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        coupon = serializer.save(course=course, created_by=request.user)
        return Response(CouponSerializer(coupon).data, status=201)


@extend_schema_view(
    get=extend_schema(
        tags=["Admin"],
        description="Lists platform-wide (not course-scoped) coupons.",
        examples=[OpenApiExample("Coupon", value=_COUPON_EXAMPLE, response_only=True)],
    ),
    post=extend_schema(
        tags=["Admin"],
        description="Creates a platform-wide coupon (not tied to a single course).",
        examples=[
            OpenApiExample(
                "Create coupon", value={**_COUPON_EXAMPLE, "course": None}, request_only=True
            )
        ],
    ),
)
class AdminCouponListCreateView(generics.ListCreateAPIView):
    serializer_class = CouponSerializer
    permission_classes = [HasPermission]
    required_permission = "coupons.manage"
    throttle_scope = "admin-write"
    queryset = Coupon.objects.all()
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


_PROMOTION_EXAMPLE = {
    "id": "e8f9a0b1-...",
    "name": "Spring Sale",
    "campaign_type": "seasonal",
    "banner_asset_key": "promotions/spring-sale.png",
    "starts_at": "2026-03-01T00:00:00Z",
    "ends_at": "2026-03-31T23:59:59Z",
    "status": "scheduled",
}


@extend_schema_view(
    get=extend_schema(
        tags=["Admin"],
        description="Lists promotional campaigns.",
        examples=[OpenApiExample("Promotion", value=_PROMOTION_EXAMPLE, response_only=True)],
    ),
    post=extend_schema(
        tags=["Admin"],
        description="Creates a promotional campaign.",
        examples=[
            OpenApiExample(
                "Create promotion",
                value={k: v for k, v in _PROMOTION_EXAMPLE.items() if k != "id"},
                request_only=True,
            )
        ],
    ),
)
class AdminPromotionListCreateView(generics.ListCreateAPIView):
    serializer_class = PromotionSerializer
    permission_classes = [HasPermission]
    required_permission = "promotions.manage"
    throttle_scope = "admin-write"
    queryset = Promotion.objects.all()
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@extend_schema_view(
    patch=extend_schema(
        tags=["Admin"],
        description="Partially updates a promotional campaign.",
        examples=[OpenApiExample("Update status", value={"status": "active"}, request_only=True)],
    ),
    put=extend_schema(
        tags=["Admin"],
        description="Replaces a promotional campaign's fields.",
        examples=[
            OpenApiExample(
                "Replace promotion",
                value={k: v for k, v in _PROMOTION_EXAMPLE.items() if k != "id"},
                request_only=True,
            )
        ],
    ),
)
class AdminPromotionUpdateView(generics.UpdateAPIView):
    serializer_class = PromotionSerializer
    permission_classes = [HasPermission]
    required_permission = "promotions.manage"
    throttle_scope = "admin-write"
    queryset = Promotion.objects.all()


# ---------- Webhooks ----------


def _process_webhook(request, provider_code, extra_headers=None):
    provider_adapter = get_provider(provider_code)
    if provider_adapter is None:
        raise NotFound(f"Unknown payment provider '{provider_code}'")

    headers = {k: v for k, v in request.headers.items()}
    if extra_headers:
        headers.update(extra_headers)

    try:
        event = provider_adapter.verify_and_parse_webhook(request.body, headers)
    except WebhookVerificationError as exc:
        raise ValidationError(f"Webhook verification failed: {exc}") from exc

    try:
        with transaction.atomic():
            WebhookEvent.objects.create(provider=provider_code, provider_event_id=event.event_id)
    except IntegrityError:
        # Already processed this exact event — ack without reprocessing.
        return Response({"status": "already_processed"})

    payment = Payment.objects.filter(
        provider=provider_code, provider_payment_id=event.provider_payment_id
    ).first()
    if payment is None:
        return Response({"status": "no_matching_payment"})

    if event.event_type == "payment.succeeded":
        payment.status = Payment.STATUS_SUCCEEDED
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "paid_at"])
        services.finalize_order_payment(payment.order)
    elif event.event_type == "payment.failed":
        payment.status = Payment.STATUS_FAILED
        payment.save(update_fields=["status"])

    return Response({"status": "processed"})


@extend_schema(
    tags=["Webhooks"],
    request=None,
    responses={200: None},
    description="Signature-verified payment provider event webhook (stripe/paypal/"
    "flutterwave/paystack). Events are deduplicated by (provider, provider_event_id) — a "
    "replayed event is acknowledged without reprocessing.",
    examples=[
        OpenApiExample("Processed", value={"status": "processed"}, response_only=True),
        OpenApiExample(
            "Already processed", value={"status": "already_processed"}, response_only=True
        ),
    ],
)
class ProviderWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, provider):
        return _process_webhook(request, provider)


@extend_schema(
    tags=["Webhooks"],
    request=None,
    responses={200: None},
    description="M-Pesa event webhook. M-Pesa's callback has no signature header, so the "
    "callback path itself carries a per-integration secret instead.",
    examples=[OpenApiExample("Processed", value={"status": "processed"}, response_only=True)],
)
class MpesaWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, secret):
        return _process_webhook(request, "mpesa", extra_headers={"X-Callback-Path-Secret": secret})
