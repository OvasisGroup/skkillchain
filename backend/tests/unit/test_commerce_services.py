from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Course
from apps.commerce import services
from apps.commerce.models import Coupon, GiftCard, Order, OrderItem
from apps.learning.models import Enrollment

pytestmark = pytest.mark.django_db


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


@pytest.fixture
def buyer(django_user_model):
    return django_user_model.objects.create_user(email="buyer@example.com", password="x")


@pytest.fixture
def course(instructor):
    c = Course.objects.create(
        owner=instructor, title="Priced Course", price_amount=Decimal("100.00")
    )
    c.status = Course.STATUS_PUBLISHED
    c.save(update_fields=["status"])
    return c


@pytest.fixture
def order(buyer, course):
    order = Order.objects.create(buyer=buyer, currency="USD")
    order.items.create(
        item_type=OrderItem.ITEM_TYPE_COURSE,
        item_id=course.id,
        unit_price=course.price_amount,
        quantity=1,
    )
    services.compute_order_totals(order)
    return order


class TestPriceItems:
    def test_prices_from_real_course_not_client_input(self, course):
        priced = services.price_items(
            [{"item_type": "course", "item_id": course.id, "quantity": 1}]
        )

        assert priced[0]["unit_price"] == course.price_amount

    def test_rejects_unpublished_course(self, instructor):
        draft = Course.objects.create(owner=instructor, title="Draft", price_amount=Decimal("50"))

        with pytest.raises(ValidationError):
            services.price_items([{"item_type": "course", "item_id": draft.id, "quantity": 1}])


class TestComputeOrderTotals:
    def test_subtotal_equals_total_with_no_discounts(self, order):
        assert order.subtotal_amount == Decimal("100.00")
        assert order.total_amount == Decimal("100.00")

    def test_percent_coupon_discounts_correctly(self, order, instructor):
        coupon = Coupon.objects.create(
            code="SAVE10",
            discount_type=Coupon.DISCOUNT_PERCENT,
            discount_value=Decimal("10"),
            created_by=instructor,
        )
        order.applied_coupon = coupon
        order.save(update_fields=["applied_coupon"])

        services.compute_order_totals(order)

        assert order.discount_amount == Decimal("10.00")
        assert order.total_amount == Decimal("90.00")

    def test_fixed_coupon_never_discounts_below_zero(self, order, instructor):
        coupon = Coupon.objects.create(
            code="HUGE",
            discount_type=Coupon.DISCOUNT_FIXED,
            discount_value=Decimal("500"),
            created_by=instructor,
        )
        order.applied_coupon = coupon
        order.save(update_fields=["applied_coupon"])

        services.compute_order_totals(order)

        assert order.discount_amount == Decimal("100.00")
        assert order.total_amount == Decimal("0.00")

    def test_gift_card_never_exceeds_its_own_balance(self, order):
        gift_card = GiftCard.objects.create(
            code="GC1", balance_amount=Decimal("30.00"), currency="USD"
        )
        order.applied_gift_card = gift_card
        order.save(update_fields=["applied_gift_card"])

        services.compute_order_totals(order)

        assert order.gift_card_amount == Decimal("30.00")
        assert order.total_amount == Decimal("70.00")


class TestApplyCoupon:
    def test_rejects_unknown_code(self, order, buyer):
        with pytest.raises(ValidationError):
            services.apply_coupon(order, "DOES-NOT-EXIST", buyer)

    def test_rejects_coupon_scoped_to_a_different_course(self, order, buyer, instructor):
        other_course = Course.objects.create(owner=instructor, title="Other")
        Coupon.objects.create(
            code="OTHER10",
            discount_type=Coupon.DISCOUNT_PERCENT,
            discount_value=Decimal("10"),
            course=other_course,
            created_by=instructor,
        )

        with pytest.raises(ValidationError):
            services.apply_coupon(order, "OTHER10", buyer)

    def test_enforces_usage_limit(self, order, buyer, instructor):
        Coupon.objects.create(
            code="LIMITED",
            discount_type=Coupon.DISCOUNT_PERCENT,
            discount_value=Decimal("10"),
            usage_limit=0,
            created_by=instructor,
        )

        with pytest.raises(ValidationError):
            services.apply_coupon(order, "LIMITED", buyer)

    def test_enforces_per_user_limit(self, order, buyer, instructor, course):
        coupon = Coupon.objects.create(
            code="ONCE",
            discount_type=Coupon.DISCOUNT_PERCENT,
            discount_value=Decimal("10"),
            per_user_limit=1,
            created_by=instructor,
        )
        # Simulate a prior redemption by this user for this coupon.
        first_order = Order.objects.create(buyer=buyer, currency="USD")
        from apps.commerce.models import CouponRedemption

        CouponRedemption.objects.create(coupon=coupon, user=buyer, order=first_order)

        with pytest.raises(ValidationError):
            services.apply_coupon(order, "ONCE", buyer)


class TestFinalizeOrderPayment:
    def test_marks_paid_creates_invoice_and_enrolls_student(self, order, buyer, course):
        services.finalize_order_payment(order)

        order.refresh_from_db()
        assert order.status == Order.STATUS_PAID
        assert hasattr(order, "invoice")
        assert Enrollment.objects.filter(student=buyer, course=course).exists()

    def test_idempotent_on_already_paid_order(self, order, buyer, course):
        services.finalize_order_payment(order)
        first_invoice_number = order.invoice.invoice_number

        services.finalize_order_payment(order)

        order.refresh_from_db()
        assert order.invoice.invoice_number == first_invoice_number
        assert Enrollment.objects.filter(student=buyer, course=course).count() == 1

    def test_deducts_gift_card_balance_only_on_finalize(self, order, buyer):
        gift_card = GiftCard.objects.create(
            code="GC2", balance_amount=Decimal("40.00"), currency="USD"
        )
        order.applied_gift_card = gift_card
        order.save(update_fields=["applied_gift_card"])
        services.compute_order_totals(order)
        assert gift_card.balance_amount == Decimal("40.00")  # untouched before finalize

        services.finalize_order_payment(order)

        gift_card.refresh_from_db()
        assert gift_card.balance_amount == Decimal("0.00")  # 40 of the 100 total applied
