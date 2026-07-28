import pytest
from django.core.management import call_command

from apps.commerce.models import Order, Payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def buyer(django_user_model):
    return django_user_model.objects.create_user(email="buyer@example.com", password="x")


def test_passes_when_ledger_is_consistent(buyer, capsys):
    order = Order.objects.create(buyer=buyer, total_amount="50.00", status=Order.STATUS_PAID)
    Payment.objects.create(
        order=order, provider="stripe", amount="50.00", status=Payment.STATUS_SUCCEEDED
    )

    call_command("verify_payment_reconciliation")

    assert "OK" in capsys.readouterr().out


def test_fails_when_paid_order_has_no_succeeded_payment(buyer):
    Order.objects.create(buyer=buyer, total_amount="50.00", status=Order.STATUS_PAID)

    with pytest.raises(SystemExit):
        call_command("verify_payment_reconciliation")


def test_fails_when_succeeded_payment_total_is_short(buyer):
    order = Order.objects.create(buyer=buyer, total_amount="100.00", status=Order.STATUS_PAID)
    Payment.objects.create(
        order=order, provider="stripe", amount="40.00", status=Payment.STATUS_SUCCEEDED
    )

    with pytest.raises(SystemExit):
        call_command("verify_payment_reconciliation")


def test_fails_when_succeeded_payment_belongs_to_non_paid_order(buyer):
    order = Order.objects.create(buyer=buyer, total_amount="50.00", status=Order.STATUS_REFUNDED)
    Payment.objects.create(
        order=order, provider="stripe", amount="50.00", status=Payment.STATUS_SUCCEEDED
    )

    with pytest.raises(SystemExit):
        call_command("verify_payment_reconciliation")
