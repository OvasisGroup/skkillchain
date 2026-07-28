"""
Verifies Order/Payment ledger consistency. Intended as a real, runnable gate
for the DR runbook (docs/06-devops-security-qa/01-devops-infra-operations.md
§6, "Verify payment reconciliation integrity") — run it against any restored
database (post-RDS-restore, post-migration, post-replay) to confirm the
financial ledger is internally consistent before resuming traffic. Also
useful outside DR as a routine ops health check.

Exits non-zero and prints every mismatch found; exits 0 with nothing to fix
otherwise.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Q, Sum

from apps.commerce.models import Order, Payment


class Command(BaseCommand):
    help = "Verify Order/Payment reconciliation integrity (see DR runbook §6)."

    def handle(self, *args, **options):
        problems: list[str] = []
        problems += self._paid_orders_without_succeeded_payment()
        problems += self._succeeded_payments_without_paid_order()
        problems += self._payment_totals_mismatch()

        if problems:
            for problem in problems:
                self.stderr.write(self.style.ERROR(problem))
            self.stderr.write(self.style.ERROR(f"{len(problems)} reconciliation problem(s) found."))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("Payment reconciliation OK: no problems found."))

    def _paid_orders_without_succeeded_payment(self) -> list[str]:
        problems = []
        paid_orders = Order.objects.filter(status=Order.STATUS_PAID)
        for order in paid_orders:
            has_succeeded = order.payments.filter(status=Payment.STATUS_SUCCEEDED).exists()
            if not has_succeeded:
                problems.append(f"Order {order.id} is 'paid' but has no succeeded Payment.")
        return problems

    def _succeeded_payments_without_paid_order(self) -> list[str]:
        problems = []
        succeeded = Payment.objects.select_related("order").filter(status=Payment.STATUS_SUCCEEDED)
        for payment in succeeded:
            if payment.order.status != Order.STATUS_PAID:
                problems.append(
                    f"Payment {payment.id} is 'succeeded' but Order {payment.order_id} "
                    f"is '{payment.order.status}', not 'paid'."
                )
        return problems

    def _payment_totals_mismatch(self) -> list[str]:
        problems = []
        paid_orders = Order.objects.filter(status=Order.STATUS_PAID).annotate(
            succeeded_total=Sum(
                "payments__amount", filter=Q(payments__status=Payment.STATUS_SUCCEEDED)
            )
        )
        for order in paid_orders:
            succeeded_total = order.succeeded_total or Decimal("0")
            if succeeded_total < order.total_amount:
                problems.append(
                    f"Order {order.id}: succeeded payments total {succeeded_total} is less "
                    f"than order total {order.total_amount}."
                )
        return problems
