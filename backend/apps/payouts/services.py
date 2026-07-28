from decimal import Decimal

from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Payout, Transaction, Wallet


def _credit_wallet(
    owner_type: str,
    owner_id,
    *,
    amount: Decimal,
    currency: str,
    reason: str,
    reference_type: str = "",
    reference_id=None,
) -> Transaction:
    """Credits a wallet (creating it on first use) and records the
    transaction that justifies the credit — the wallet balance is always
    the sum of its own transaction ledger, never set directly outside of
    this ledger-writing path."""
    wallet, _ = Wallet.objects.get_or_create(
        owner_type=owner_type, owner_id=owner_id, currency=currency
    )
    with db_transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(id=wallet.id)
        wallet.balance_amount = wallet.balance_amount + amount
        wallet.save(update_fields=["balance_amount"])
        return Transaction.objects.create(
            wallet=wallet,
            direction=Transaction.DIRECTION_CREDIT,
            amount=amount,
            reason=reason,
            reference_type=reference_type,
            reference_id=reference_id,
        )


def credit_instructor_wallet(
    instructor_id,
    *,
    amount: Decimal,
    currency: str,
    reason: str,
    reference_type: str = "",
    reference_id=None,
) -> Transaction:
    return _credit_wallet(
        Wallet.OWNER_INSTRUCTOR,
        instructor_id,
        amount=amount,
        currency=currency,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
    )


def credit_affiliate_wallet(
    affiliate_user_id,
    *,
    amount: Decimal,
    currency: str,
    reason: str,
    reference_type: str = "",
    reference_id=None,
) -> Transaction:
    return _credit_wallet(
        Wallet.OWNER_AFFILIATE,
        affiliate_user_id,
        amount=amount,
        currency=currency,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
    )


@db_transaction.atomic
def request_payout(instructor, owner_type: str = Wallet.OWNER_INSTRUCTOR) -> Payout:
    """
    Sweeps every credit/debit transaction not yet attached to a payout
    into a new one, using the wallet's own running balance as the payout
    amount. A live-verification and a test both independently re-sum the
    swept transactions from the ledger and assert they equal the payout's
    stored amount_gross — this function's arithmetic is not trusted blind.

    No provider payout execution exists (no bank/mobile-money rail
    adapter is wired up) — this performs the internal ledger accounting
    only and marks the payout "paid" immediately, matching the pattern of
    naming a real gap (see M-Pesa/coding-exercise-sandbox notes) rather
    than pretending money actually moved.
    """
    wallet = (
        Wallet.objects.select_for_update()
        .filter(owner_type=owner_type, owner_id=instructor.id)
        .first()
    )
    if wallet is None or wallet.balance_amount <= 0:
        raise ValidationError("No available balance to pay out.")

    unswept = wallet.transactions.filter(payout__isnull=True).order_by("created_at")
    earliest = unswept.first()
    if earliest is None:
        # Shouldn't happen — a positive balance implies at least one
        # unswept credit — but fail loudly instead of crashing on
        # `.created_at` of None if that invariant is ever violated.
        raise ValidationError("No available balance to pay out.")
    period_start = earliest.created_at
    period_end = timezone.now()
    amount = wallet.balance_amount

    payout = Payout.objects.create(
        instructor=instructor,
        period_start=period_start,
        period_end=period_end,
        amount_gross=amount,
        amount_net=amount,
        status=Payout.STATUS_PAID,
        paid_at=period_end,
    )
    unswept.update(payout=payout)
    Transaction.objects.create(
        wallet=wallet,
        direction=Transaction.DIRECTION_DEBIT,
        amount=amount,
        reason="payout",
        reference_type="Payout",
        reference_id=payout.id,
        payout=payout,
    )
    wallet.balance_amount = Decimal("0")
    wallet.save(update_fields=["balance_amount"])
    return payout
