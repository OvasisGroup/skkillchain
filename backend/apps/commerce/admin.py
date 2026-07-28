from django.contrib import admin

from .models import (
    Coupon,
    CouponRedemption,
    GiftCard,
    GiftCardRedemption,
    Invoice,
    Order,
    OrderItem,
    Payment,
    PaymentMethod,
    Promotion,
    Refund,
    WebhookEvent,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "buyer", "status", "total_amount", "currency", "created_at"]
    list_filter = ["status", "currency"]
    search_fields = ["buyer__email", "id"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "provider", "status", "amount", "currency", "paid_at"]
    list_filter = ["provider", "status"]
    search_fields = ["order__buyer__email", "provider_payment_id"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ["id", "payment", "amount", "status", "requested_at"]
    list_filter = ["status"]
    readonly_fields = ["id", "requested_at"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "order", "issued_at"]
    search_fields = ["invoice_number", "order__buyer__email"]
    readonly_fields = ["id", "issued_at"]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "discount_type", "discount_value", "course", "usage_limit"]
    search_fields = ["code"]


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ["name", "status", "starts_at", "ends_at"]
    list_filter = ["status"]


@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = ["code", "balance_amount", "currency", "expires_at"]
    search_fields = ["code"]


admin.site.register(PaymentMethod)
admin.site.register(CouponRedemption)
admin.site.register(GiftCardRedemption)
admin.site.register(WebhookEvent)
