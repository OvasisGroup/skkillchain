from decimal import Decimal

import pytest
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from apps.payouts import services
from apps.payouts.models import Transaction, Wallet

pytestmark = pytest.mark.django_db


@pytest.fixture
def instructor(django_user_model):
    return django_user_model.objects.create_user(email="instructor@example.com", password="x")


class TestCreditInstructorWallet:
    def test_creates_wallet_on_first_credit(self, instructor):
        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("70.00"), currency="USD", reason="course_sale"
        )

        wallet = Wallet.objects.get(owner_type=Wallet.OWNER_INSTRUCTOR, owner_id=instructor.id)
        assert wallet.balance_amount == Decimal("70.00")

    def test_accumulates_across_multiple_credits(self, instructor):
        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("30.00"), currency="USD", reason="course_sale"
        )
        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("45.00"), currency="USD", reason="course_sale"
        )

        wallet = Wallet.objects.get(owner_type=Wallet.OWNER_INSTRUCTOR, owner_id=instructor.id)
        assert wallet.balance_amount == Decimal("75.00")
        assert wallet.transactions.count() == 2


class TestRequestPayout:
    def test_rejects_when_no_wallet_exists(self, instructor):
        with pytest.raises(ValidationError):
            services.request_payout(instructor)

    def test_rejects_zero_balance(self, instructor):
        Wallet.objects.create(
            owner_type=Wallet.OWNER_INSTRUCTOR, owner_id=instructor.id, currency="USD"
        )

        with pytest.raises(ValidationError):
            services.request_payout(instructor)

    def test_payout_amount_matches_independently_summed_ledger(self, instructor):
        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("40.00"), currency="USD", reason="course_sale"
        )
        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("25.50"), currency="USD", reason="course_sale"
        )

        payout = services.request_payout(instructor)

        # The reconciliation itself: re-derive the payout total from the
        # ledger with a query completely independent of request_payout's
        # own arithmetic, rather than trusting its stored amount_gross.
        independently_summed = Transaction.objects.filter(
            payout=payout, direction=Transaction.DIRECTION_CREDIT
        ).aggregate(total=Sum("amount"))["total"]

        assert independently_summed == Decimal("65.50")
        assert payout.amount_gross == independently_summed
        assert payout.amount_net == independently_summed

    def test_wallet_balance_zeroed_after_payout(self, instructor):
        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("100.00"), currency="USD", reason="course_sale"
        )

        services.request_payout(instructor)

        wallet = Wallet.objects.get(owner_type=Wallet.OWNER_INSTRUCTOR, owner_id=instructor.id)
        assert wallet.balance_amount == Decimal("0.00")

    def test_second_payout_only_covers_transactions_since_the_first(self, instructor):
        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("50.00"), currency="USD", reason="course_sale"
        )
        first_payout = services.request_payout(instructor)

        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("20.00"), currency="USD", reason="course_sale"
        )
        second_payout = services.request_payout(instructor)

        assert first_payout.amount_gross == Decimal("50.00")
        assert second_payout.amount_gross == Decimal("20.00")
        # The first payout's swept transactions are untouched by the second.
        first_credit_sum = Transaction.objects.filter(
            payout=first_payout, direction=Transaction.DIRECTION_CREDIT
        ).aggregate(total=Sum("amount"))["total"]
        assert first_credit_sum == Decimal("50.00")

    def test_wallet_balance_always_equals_credits_minus_debits(self, instructor):
        """A second, independent reconciliation: the wallet's own running
        balance must always equal the full transaction ledger's
        credit-minus-debit sum, not just what request_payout claims."""
        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("80.00"), currency="USD", reason="course_sale"
        )
        services.request_payout(instructor)
        services.credit_instructor_wallet(
            instructor.id, amount=Decimal("15.00"), currency="USD", reason="course_sale"
        )

        wallet = Wallet.objects.get(owner_type=Wallet.OWNER_INSTRUCTOR, owner_id=instructor.id)
        credits = Transaction.objects.filter(
            wallet=wallet, direction=Transaction.DIRECTION_CREDIT
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        debits = Transaction.objects.filter(
            wallet=wallet, direction=Transaction.DIRECTION_DEBIT
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        assert wallet.balance_amount == credits - debits
        assert wallet.balance_amount == Decimal("15.00")
