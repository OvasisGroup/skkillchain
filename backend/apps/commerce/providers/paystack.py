import hashlib
import hmac
import json

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

_API_BASE = "https://api.paystack.co"

_EVENT_TYPE_MAP = {
    "charge.success": "payment.succeeded",
    "charge.failed": "payment.failed",
}


class PaystackPaymentProvider(PaymentProvider):
    code = "paystack"

    def create_payment(self, *, amount, currency, order_id):
        try:
            response = requests.post(
                f"{_API_BASE}/transaction/initialize",
                headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"},
                json={
                    "amount": int(amount * 100),  # kobo/minor units
                    "currency": currency.upper(),
                    "reference": order_id,
                    "metadata": {"order_id": order_id},
                },
                timeout=10,
            )
        except requests.exceptions.RequestException as exc:
            raise PaymentProviderError(f"Paystack request failed: {exc}") from exc
        if response.status_code != 200 or not response.json().get("status"):
            raise PaymentProviderError(f"Paystack transaction init failed: {response.text}")
        data = response.json()["data"]
        return PaymentInit(
            provider_payment_id=data["reference"],
            client_secret=None,
            redirect_url=data["authorization_url"],
        )

    def verify_and_parse_webhook(self, raw_body: bytes, headers: dict) -> WebhookEventData:
        signature = headers.get("X-Paystack-Signature", "")
        expected = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(), raw_body, hashlib.sha512
        ).hexdigest()
        if not signature or not hmac.compare_digest(expected, signature):
            raise WebhookVerificationError("Paystack signature mismatch.")

        event = json.loads(raw_body)
        event_type = _EVENT_TYPE_MAP.get(event.get("event", ""))
        if event_type is None:
            raise WebhookVerificationError(f"Unhandled Paystack event type: {event.get('event')}")

        return WebhookEventData(
            event_id=str(event["data"]["id"]),
            event_type=event_type,
            provider_payment_id=event["data"]["reference"],
        )

    def refund_payment(self, provider_payment_id, *, amount):
        try:
            response = requests.post(
                f"{_API_BASE}/refund",
                headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"},
                json={"transaction": provider_payment_id, "amount": int(amount * 100)},
                timeout=10,
            )
        except requests.exceptions.RequestException as exc:
            raise PaymentProviderError(f"Paystack request failed: {exc}") from exc
        if response.status_code != 200 or not response.json().get("status"):
            raise PaymentProviderError(f"Paystack refund failed: {response.text}")
        data = response.json()["data"]
        return RefundResult(provider_refund_id=str(data["id"]), status="pending")
