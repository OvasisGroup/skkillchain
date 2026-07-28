from rest_framework import serializers

from .models import Coupon, GiftCard, Invoice, Order, OrderItem, Payment, Promotion, Refund


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "item_type", "item_id", "unit_price", "quantity"]


class OrderItemInputSerializer(serializers.Serializer):
    item_type = serializers.ChoiceField(choices=OrderItem.ITEM_TYPE_CHOICES)
    item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(default=1, min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("An order needs at least one item.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "subtotal_amount",
            "discount_amount",
            "tax_amount",
            "gift_card_amount",
            "total_amount",
            "currency",
            "items",
            "created_at",
        ]


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField()


class ApplyGiftCardSerializer(serializers.Serializer):
    code = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


PAYMENT_PROVIDER_CHOICES = [
    ("stripe", "Stripe"),
    ("paypal", "PayPal"),
    ("flutterwave", "Flutterwave"),
    ("paystack", "Paystack"),
    ("mpesa", "M-Pesa"),
]


class PaySerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=PAYMENT_PROVIDER_CHOICES)
    # Only meaningful for mpesa — see apps/commerce/providers/mpesa.py.
    phone_number = serializers.CharField(required=False, allow_blank=True)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "provider",
            "provider_payment_id",
            "status",
            "amount",
            "currency",
            "paid_at",
        ]


class PayResponseSerializer(serializers.Serializer):
    payment = PaymentSerializer()
    client_secret = serializers.CharField(allow_null=True)
    redirect_url = serializers.CharField(allow_null=True)


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["id", "order", "invoice_number", "tax_metadata", "issued_at"]


class RefundCreateSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField(required=False, allow_blank=True)


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = [
            "id",
            "payment",
            "provider_refund_id",
            "amount",
            "reason",
            "status",
            "requested_at",
        ]


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            "id",
            "code",
            "discount_type",
            "discount_value",
            "valid_from",
            "valid_to",
            "usage_limit",
            "per_user_limit",
            "promotion",
            "course",
        ]
        read_only_fields = ["id"]


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = [
            "id",
            "name",
            "campaign_type",
            "banner_asset_key",
            "starts_at",
            "ends_at",
            "status",
        ]
        read_only_fields = ["id"]


class GiftCardBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftCard
        fields = ["code", "balance_amount", "currency", "expires_at"]
