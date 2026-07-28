from decimal import Decimal

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
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


@extend_schema(tags=["Payments"], request=OrderCreateSerializer, responses={201: OrderSerializer})
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


@extend_schema(tags=["Payments"], request=ApplyCouponSerializer, responses={200: OrderSerializer})
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


@extend_schema(tags=["Payments"], request=ApplyGiftCardSerializer, responses={200: OrderSerializer})
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


@extend_schema(tags=["Payments"], request=PaySerializer, responses={200: PayResponseSerializer})
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


@extend_schema(tags=["Payments"])
class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Payment.objects.filter(order__buyer=self.request.user).select_related("order")


@extend_schema(tags=["Payments"])
class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Invoice.objects.filter(order__buyer=self.request.user).select_related("order")


@extend_schema(tags=["Payments"], request=RefundCreateSerializer, responses={201: RefundSerializer})
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


@extend_schema(tags=["Payments"], responses={200: GiftCardBalanceSerializer})
class GiftCardBalanceView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, code):
        gift_card = get_object_or_404(GiftCard, code=code)
        return Response(GiftCardBalanceSerializer(gift_card).data)


# ---------- Instructor / Admin coupon & promotion authoring ----------


@extend_schema(tags=["Instructor"], request=CouponSerializer, responses={201: CouponSerializer})
class InstructorCouponCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "financial-write"

    def post(self, request, course_id):
        course = _owned_course_or_403(course_id, request.user)
        serializer = CouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        coupon = serializer.save(course=course, created_by=request.user)
        return Response(CouponSerializer(coupon).data, status=201)


@extend_schema(tags=["Admin"])
class AdminCouponListCreateView(generics.ListCreateAPIView):
    serializer_class = CouponSerializer
    permission_classes = [HasPermission]
    required_permission = "coupons.manage"
    throttle_scope = "admin-write"
    queryset = Coupon.objects.all()
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@extend_schema(tags=["Admin"])
class AdminPromotionListCreateView(generics.ListCreateAPIView):
    serializer_class = PromotionSerializer
    permission_classes = [HasPermission]
    required_permission = "promotions.manage"
    throttle_scope = "admin-write"
    queryset = Promotion.objects.all()
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@extend_schema(tags=["Admin"])
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


@extend_schema(tags=["Webhooks"], request=None, responses={200: None})
class ProviderWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, provider):
        return _process_webhook(request, provider)


@extend_schema(tags=["Webhooks"], request=None, responses={200: None})
class MpesaWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, secret):
        return _process_webhook(request, "mpesa", extra_headers={"X-Callback-Path-Secret": secret})
