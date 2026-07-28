import uuid
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.affiliates.models import AffiliateAccount, AffiliateCommission, AffiliateReferral
from apps.billing.models import Plan, Subscription
from apps.catalog.models import Course
from apps.learning.models import Enrollment
from apps.payouts.services import credit_affiliate_wallet, credit_instructor_wallet

from .models import (
    Coupon,
    CouponRedemption,
    GiftCard,
    GiftCardRedemption,
    Invoice,
    Order,
    OrderItem,
)


def price_items(items_data: list[dict]) -> list[dict]:
    """Validates each requested item against the real, current Course/Plan
    record and prices it server-side — a client-submitted unit_price is
    never trusted, even if one were accepted in the request."""
    priced = []
    for item in items_data:
        if item["item_type"] == OrderItem.ITEM_TYPE_COURSE:
            course = Course.objects.filter(
                id=item["item_id"], status=Course.STATUS_PUBLISHED
            ).first()
            if course is None:
                raise ValidationError(f"Course {item['item_id']} is not available for purchase.")
            priced.append(
                {
                    "item_type": OrderItem.ITEM_TYPE_COURSE,
                    "item_id": course.id,
                    "unit_price": course.price_amount,
                    "quantity": item.get("quantity", 1),
                    "currency": course.currency,
                }
            )
        elif item["item_type"] == OrderItem.ITEM_TYPE_PLAN:
            plan = Plan.objects.filter(id=item["item_id"], is_active=True).first()
            if plan is None:
                raise ValidationError(f"Plan {item['item_id']} is not available for purchase.")
            priced.append(
                {
                    "item_type": OrderItem.ITEM_TYPE_PLAN,
                    "item_id": plan.id,
                    "unit_price": plan.price_amount,
                    "quantity": 1,  # a subscription plan is never bought in bulk
                    "currency": plan.currency,
                }
            )
        else:
            raise ValidationError(f"Unsupported item_type '{item['item_type']}'.")
    return priced


def compute_order_totals(order: Order) -> None:
    """Recomputes every total field from the order's own persisted state
    (items, applied_coupon, applied_gift_card) — called after any mutation
    so the stored total_amount is always derived, never hand-set."""
    subtotal = sum((item.unit_price * item.quantity for item in order.items.all()), Decimal("0"))
    order.subtotal_amount = subtotal

    discount = Decimal("0")
    if (coupon := order.applied_coupon) is not None:
        if coupon.discount_type == Coupon.DISCOUNT_PERCENT:
            discount = subtotal * coupon.discount_value / Decimal("100")
        else:
            discount = coupon.discount_value
    order.discount_amount = min(discount, subtotal)

    remaining_after_discount = max(subtotal - order.discount_amount, Decimal("0"))

    gift_card_amount = Decimal("0")
    if (gift_card := order.applied_gift_card) is not None:
        gift_card_amount = min(gift_card.balance_amount, remaining_after_discount)
    order.gift_card_amount = gift_card_amount

    # No tax jurisdiction engine exists yet — tax_amount stays 0 until one
    # is built; this is a deliberate scope cut, not a bug.
    order.total_amount = max(
        remaining_after_discount - gift_card_amount + order.tax_amount, Decimal("0")
    )
    order.save(
        update_fields=["subtotal_amount", "discount_amount", "gift_card_amount", "total_amount"]
    )


def apply_coupon(order: Order, code: str, user) -> Order:
    coupon = Coupon.objects.filter(code=code).first()
    if coupon is None:
        raise ValidationError("Invalid coupon code.")

    now = timezone.now()
    if coupon.valid_from and now < coupon.valid_from:
        raise ValidationError("This coupon is not active yet.")
    if coupon.valid_to and now > coupon.valid_to:
        raise ValidationError("This coupon has expired.")
    if coupon.course_id and not order.items.filter(item_id=coupon.course_id).exists():
        raise ValidationError("This coupon does not apply to any item in your order.")
    if coupon.usage_limit is not None and coupon.redemptions.count() >= coupon.usage_limit:
        raise ValidationError("This coupon has reached its usage limit.")
    if (
        coupon.per_user_limit is not None
        and coupon.redemptions.filter(user=user).count() >= coupon.per_user_limit
    ):
        raise ValidationError("You have already used this coupon the maximum number of times.")

    order.applied_coupon = coupon
    order.save(update_fields=["applied_coupon"])
    compute_order_totals(order)
    return order


def apply_gift_card(order: Order, code: str, requested_amount: Decimal | None = None) -> Order:
    gift_card = GiftCard.objects.filter(code=code).first()
    if gift_card is None:
        raise ValidationError("Invalid gift card code.")
    if gift_card.is_expired:
        raise ValidationError("This gift card has expired.")
    if gift_card.balance_amount <= 0:
        raise ValidationError("This gift card has no remaining balance.")

    order.applied_gift_card = gift_card
    order.save(update_fields=["applied_gift_card"])
    compute_order_totals(order)

    # requested_amount only ever narrows how much of the order the gift
    # card covers — compute_order_totals already clamped gift_card_amount
    # to both the card's real balance and the order's remaining total, so
    # a smaller explicit request just re-clamps on top of that.
    if requested_amount is not None and requested_amount < order.gift_card_amount:
        order.gift_card_amount = requested_amount
        order.total_amount = max(
            order.subtotal_amount - order.discount_amount - requested_amount + order.tax_amount,
            Decimal("0"),
        )
        order.save(update_fields=["gift_card_amount", "total_amount"])
    return order


def _generate_invoice_number() -> str:
    return f"INV-{uuid.uuid4().hex[:10].upper()}"


def capture_referral(order: Order, referral_code: str, buyer) -> None:
    """Best-effort: an unknown or self-referral code just doesn't
    attribute a referral — it never blocks checkout, since the code is
    incidental to the purchase the buyer actually wants."""
    affiliate = AffiliateAccount.objects.filter(referral_code=referral_code).first()
    if affiliate is None or affiliate.user_id == buyer.id:
        return
    AffiliateReferral.objects.get_or_create(
        order=order, defaults={"affiliate": affiliate, "referred_user": buyer}
    )


@transaction.atomic
def finalize_order_payment(order: Order) -> None:
    """
    Called once a payment has genuinely succeeded (from the pay-confirmation
    path or a verified webhook) — idempotent, so a replayed "succeeded"
    event for an already-paid order is a safe no-op rather than
    double-enrolling or double-spending a gift card.
    """
    order = Order.objects.select_for_update().get(id=order.id)
    if order.status == Order.STATUS_PAID:
        return

    if order.applied_coupon_id:
        CouponRedemption.objects.get_or_create(
            order=order, defaults={"coupon": order.applied_coupon, "user": order.buyer}
        )

    if order.applied_gift_card_id:
        gift_card = GiftCard.objects.select_for_update().get(id=order.applied_gift_card_id)
        amount = min(order.gift_card_amount, gift_card.balance_amount)
        gift_card.balance_amount = gift_card.balance_amount - amount
        gift_card.save(update_fields=["balance_amount"])
        GiftCardRedemption.objects.get_or_create(
            order=order, defaults={"gift_card": gift_card, "amount_applied": amount}
        )

    order.status = Order.STATUS_PAID
    order.save(update_fields=["status"])

    Invoice.objects.get_or_create(
        order=order, defaults={"invoice_number": _generate_invoice_number()}
    )

    for item in order.items.filter(item_type=OrderItem.ITEM_TYPE_COURSE):
        Enrollment.objects.get_or_create(
            course_id=item.item_id,
            student=order.buyer,
            defaults={"source": Enrollment.SOURCE_PURCHASE},
        )
        course = Course.objects.filter(id=item.item_id).first()
        if course is not None and item.unit_price > 0:
            instructor_share = (
                item.unit_price * item.quantity * (Decimal("1") - settings.PLATFORM_COMMISSION_RATE)
            )
            credit_instructor_wallet(
                course.owner_id,
                amount=instructor_share,
                currency=order.currency,
                reason="course_sale",
                reference_type="Payment",
                reference_id=order.id,
            )

    for item in order.items.filter(item_type=OrderItem.ITEM_TYPE_PLAN):
        plan = Plan.objects.get(id=item.item_id)
        Subscription.objects.get_or_create(
            subscriber_type=Subscription.SUBSCRIBER_USER,
            subscriber_id=order.buyer_id,
            plan=plan,
            status=Subscription.STATUS_ACTIVE,
            defaults={"renews_at": timezone.now() + plan.interval_timedelta},
        )

    referral = AffiliateReferral.objects.filter(
        order=order, status=AffiliateReferral.STATUS_PENDING
    ).first()
    if referral is not None and order.subtotal_amount > 0:
        # Based on subtotal (gross item price), not total_amount — same
        # basis as the instructor revenue-share above, which also credits
        # from item.unit_price regardless of any gift-card/coupon
        # reduction. A gift-card-covered sale still counts as a
        # successful referral; the gift card's own balance was itself
        # funded with real money at some earlier point.
        commission_amount = order.subtotal_amount * (
            referral.affiliate.commission_rate / Decimal("100")
        )
        AffiliateCommission.objects.get_or_create(
            referral=referral, defaults={"commission_amount": commission_amount}
        )
        credit_affiliate_wallet(
            referral.affiliate.user_id,
            amount=commission_amount,
            currency=order.currency,
            reason="affiliate_commission",
            reference_type="Order",
            reference_id=order.id,
        )
        referral.status = AffiliateReferral.STATUS_CONVERTED
        referral.save(update_fields=["status"])
