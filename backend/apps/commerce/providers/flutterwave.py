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

_API_BASE = "https://api.flutterwave.com/v3"

_EVENT_TYPE_MAP = {
    "successful": "payment.succeeded",
    "failed": "payment.failed",
}


class FlutterwavePaymentProvider(PaymentProvider):
    code = "flutterwave"

    def create_payment(self, *, amount, currency, order_id):
        try:
            response = requests.post(
                f"{_API_BASE}/payments",
                headers={"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"},
                json={
                    "tx_ref": order_id,
                    "amount": str(amount),
                    "currency": currency.upper(),
                    "redirect_url": settings.PUBLIC_APP_URL + "/checkout/return",
                },
                timeout=10,
            )
        except requests.exceptions.RequestException as exc:
            raise PaymentProviderError(f"Flutterwave request failed: {exc}") from exc
        if response.status_code != 200 or response.json().get("status") != "success":
            raise PaymentProviderError(f"Flutterwave payment init failed: {response.text}")
        data = response.json()["data"]
        return PaymentInit(
            provider_payment_id=order_id, client_secret=None, redirect_url=data["link"]
        )

    def verify_and_parse_webhook(self, raw_body: bytes, headers: dict) -> WebhookEventData:
        # Flutterwave's model is a static shared secret, not a per-request
        # HMAC: you configure a "secret hash" in the dashboard and they
        # echo it back verbatim in this header — verification is a
        # constant-time string comparison, not a signature computation.
        received_hash = headers.get("Verif-Hash", "")
        if not received_hash or not hmac.compare_digest(
            received_hash, settings.FLUTTERWAVE_WEBHOOK_SECRET_HASH
        ):
            raise WebhookVerificationError("Flutterwave verif-hash mismatch.")

        event = json.loads(raw_body)
        data = event.get("data", {})
        event_type = _EVENT_TYPE_MAP.get(data.get("status", ""))
        if event_type is None:
            raise WebhookVerificationError(f"Unhandled Flutterwave status: {data.get('status')}")

        return WebhookEventData(
            event_id=str(data["id"]), event_type=event_type, provider_payment_id=data["tx_ref"]
        )

    def refund_payment(self, provider_payment_id, *, amount):
        try:
            response = requests.post(
                f"{_API_BASE}/transactions/{provider_payment_id}/refund",
                headers={"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"},
                json={"amount": str(amount)},
                timeout=10,
            )
        except requests.exceptions.RequestException as exc:
            raise PaymentProviderError(f"Flutterwave request failed: {exc}") from exc
        if response.status_code != 200 or response.json().get("status") != "success":
            raise PaymentProviderError(f"Flutterwave refund failed: {response.text}")
        data = response.json()["data"]
        return RefundResult(provider_refund_id=str(data["id"]), status="pending")
