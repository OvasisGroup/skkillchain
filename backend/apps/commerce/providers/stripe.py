import hashlib
import hmac
import json
import time

import requests
from django.conf import settings

from .base import (
    PaymentInit,
    PaymentProvider,
    PaymentProviderError,
    RefundResult,
    WebhookEventData,
    WebhookVerificationError,
)

_API_BASE = "https://api.stripe.com/v1"

_EVENT_TYPE_MAP = {
    "payment_intent.succeeded": "payment.succeeded",
    "payment_intent.payment_failed": "payment.failed",
}


class StripePaymentProvider(PaymentProvider):
    code = "stripe"

    def create_payment(self, *, amount, currency, order_id):
        try:
            response = requests.post(
                f"{_API_BASE}/payment_intents",
                auth=(settings.STRIPE_SECRET_KEY, ""),
                data={
                    "amount": int(amount * 100),  # Stripe amounts are minor units
                    "currency": currency.lower(),
                    "metadata[order_id]": order_id,
                },
                timeout=10,
            )
        except requests.exceptions.RequestException as exc:
            raise PaymentProviderError(f"Stripe request failed: {exc}") from exc
        if response.status_code != 200:
            raise PaymentProviderError(f"Stripe payment_intent creation failed: {response.text}")
        data = response.json()
        return PaymentInit(
            provider_payment_id=data["id"], client_secret=data["client_secret"], redirect_url=None
        )

    def verify_and_parse_webhook(self, raw_body: bytes, headers: dict) -> WebhookEventData:
        signature_header = headers.get("Stripe-Signature", "")
        parts = dict(item.split("=", 1) for item in signature_header.split(",") if "=" in item)
        timestamp = parts.get("t")
        signature = parts.get("v1")
        if not timestamp or not signature:
            raise WebhookVerificationError("Missing Stripe-Signature timestamp/signature.")

        signed_payload = f"{timestamp}.{raw_body.decode()}".encode()
        expected = hmac.new(
            settings.STRIPE_WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise WebhookVerificationError("Stripe signature mismatch.")

        # Stripe tolerates a few minutes of clock skew but rejects stale
        # timestamps to stop replay of an old, validly-signed payload.
        if abs(time.time() - int(timestamp)) > 300:
            raise WebhookVerificationError("Stripe webhook timestamp is too old.")

        event = json.loads(raw_body)
        event_type = _EVENT_TYPE_MAP.get(event.get("type", ""))
        if event_type is None:
            raise WebhookVerificationError(f"Unhandled Stripe event type: {event.get('type')}")

        return WebhookEventData(
            event_id=event["id"],
            event_type=event_type,
            provider_payment_id=event["data"]["object"]["id"],
        )

    def refund_payment(self, provider_payment_id, *, amount):
        try:
            response = requests.post(
                f"{_API_BASE}/refunds",
                auth=(settings.STRIPE_SECRET_KEY, ""),
                data={"payment_intent": provider_payment_id, "amount": int(amount * 100)},
                timeout=10,
            )
        except requests.exceptions.RequestException as exc:
            raise PaymentProviderError(f"Stripe request failed: {exc}") from exc
        if response.status_code != 200:
            raise PaymentProviderError(f"Stripe refund failed: {response.text}")
        data = response.json()
        status = "succeeded" if data.get("status") == "succeeded" else "pending"
        return RefundResult(provider_refund_id=data["id"], status=status)
