from django.urls import path

from . import views

urlpatterns = [
    path("checkout/orders/", views.CheckoutOrderCreateView.as_view(), name="checkout-order-create"),
    path(
        "checkout/orders/<uuid:order_id>/apply-coupon/",
        views.ApplyCouponView.as_view(),
        name="checkout-apply-coupon",
    ),
    path(
        "checkout/orders/<uuid:order_id>/apply-gift-card/",
        views.ApplyGiftCardView.as_view(),
        name="checkout-apply-gift-card",
    ),
    path("checkout/orders/<uuid:order_id>/pay/", views.PayOrderView.as_view(), name="checkout-pay"),
    path(
        "checkout/orders/<uuid:order_id>/",
        views.OrderDetailView.as_view(),
        name="checkout-order-detail",
    ),
    path("payments/", views.PaymentListView.as_view(), name="payment-list"),
    path("invoices/", views.InvoiceListView.as_view(), name="invoice-list"),
    path("refunds/", views.RefundCreateView.as_view(), name="refund-create"),
    path("gift-cards/<str:code>/", views.GiftCardBalanceView.as_view(), name="gift-card-balance"),
    path(
        "instructor/courses/<uuid:course_id>/coupons/",
        views.InstructorCouponCreateView.as_view(),
        name="instructor-coupon-create",
    ),
    path(
        "admin/coupons/", views.AdminCouponListCreateView.as_view(), name="admin-coupon-list-create"
    ),
    path(
        "admin/promotions/",
        views.AdminPromotionListCreateView.as_view(),
        name="admin-promotion-list-create",
    ),
    path(
        "admin/promotions/<uuid:pk>/",
        views.AdminPromotionUpdateView.as_view(),
        name="admin-promotion-update",
    ),
    path("webhooks/mpesa/<str:secret>/", views.MpesaWebhookView.as_view(), name="webhook-mpesa"),
    path("webhooks/<str:provider>/", views.ProviderWebhookView.as_view(), name="webhook-provider"),
]
