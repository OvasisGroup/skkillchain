from dataclasses import dataclass


class WebhookVerificationError(Exception):
    """Raised when a webhook's signature can't be verified — the view maps
    this to a 400 rather than processing an unverified payload."""


class PaymentProviderError(Exception):
    """Raised on any failure talking to the provider's API."""


@dataclass
class PaymentInit:
    provider_payment_id: str
    # Exactly one of these is set, depending on the provider's integration
    # model: Stripe returns a client_secret for its client-side SDK to
    # confirm; the redirect-based providers return a hosted checkout URL.
    client_secret: str | None
    redirect_url: str | None


@dataclass
class WebhookEventData:
    event_id: str
    event_type: str  # normalized: "payment.succeeded" | "payment.failed"
    provider_payment_id: str


@dataclass
class RefundResult:
    provider_refund_id: str
    status: str  # "succeeded" | "pending" | "failed"


class PaymentProvider:
    code: str = ""

    def create_payment(self, *, amount, currency: str, order_id: str) -> PaymentInit:
        raise NotImplementedError

    def verify_and_parse_webhook(self, raw_body: bytes, headers: dict) -> WebhookEventData:
        """Verifies the signature and parses the event in one call — a
        caller should never be able to get parsed event data without the
        signature having been checked first. Raises WebhookVerificationError
        on any failure."""
        raise NotImplementedError

    def refund_payment(self, provider_payment_id: str, *, amount) -> RefundResult:
        raise NotImplementedError
