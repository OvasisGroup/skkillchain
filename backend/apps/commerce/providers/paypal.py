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

_API_BASE = "https://api-m.paypal.com"

_EVENT_TYPE_MAP = {
    "PAYMENT.CAPTURE.COMPLETED": "payment.succeeded",
    "PAYMENT.CAPTURE.DENIED": "payment.failed",
}


class PayPalPaymentProvider(PaymentProvider):
    code = "paypal"

    def _access_token(self) -> str:
        try:
            response = requests.post(
                f"{_API_BASE}/v1/oauth2/token",
                auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
                data={"grant_type": "client_credentials"},
                timeout=10,
            )
        except requests.exceptions.RequestException as exc:
            raise PaymentProviderError(f"PayPal auth request failed: {exc}") from exc
        if response.status_code != 200:
            raise PaymentProviderError(f"PayPal auth failed: {response.text}")
        return response.json()["access_token"]

    def create_payment(self, *, amount, currency, order_id):
        token = self._access_token()
        try:
            response = requests.post(
                f"{_API_BASE}/v2/checkout/orders",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "intent": "CAPTURE",
                    "purchase_units": [
                        {
                            "reference_id": order_id,
                            "amount": {"currency_code": currency.upper(), "value": str(amount)},
                        }
                    ],
                },
                timeout=10,
            )
        except requests.exceptions.RequestException as exc:
            raise PaymentProviderError(f"PayPal request failed: {exc}") from exc
        if response.status_code not in (200, 201):
            raise PaymentProviderError(f"PayPal order creation failed: {response.text}")
        data = response.json()
        approve_link = next(
            (link["href"] for link in data["links"] if link["rel"] == "approve"), None
        )
        return PaymentInit(
            provider_payment_id=data["id"], client_secret=None, redirect_url=approve_link
        )

    def verify_and_parse_webhook(self, raw_body: bytes, headers: dict) -> WebhookEventData:
        # Unlike Stripe/Paystack's local HMAC check, PayPal has no
        # documented way to verify a webhook signature locally — it
        # requires calling their own verification API with the
        # transmission headers and the raw event body.
        token = self._access_token()
        try:
            response = requests.post(
                f"{_API_BASE}/v1/notifications/verify-webhook-signature",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "auth_algo": headers.get("Paypal-Auth-Algo"),
                    "cert_url": headers.get("Paypal-Cert-Url"),
                    "transmission_id": headers.get("Paypal-Transmission-Id"),
                    "transmission_sig": headers.get("Paypal-Transmission-Sig"),
                    "transmission_time": headers.get("Paypal-Transmission-Time"),
                    "webhook_id": settings.PAYPAL_WEBHOOK_ID,
                    "webhook_event": json.loads(raw_body),
                },
                timeout=10,
            )
        except requests.exceptions.RequestException as exc:
            raise WebhookVerificationError(f"PayPal verification request failed: {exc}") from exc
        if response.status_code != 200 or response.json().get("verification_status") != "SUCCESS":
            raise WebhookVerificationError("PayPal webhook signature verification failed.")

        event = json.loads(raw_body)
        event_type = _EVENT_TYPE_MAP.get(event.get("event_type", ""))
        if event_type is None:
            raise WebhookVerificationError(
                f"Unhandled PayPal event type: {event.get('event_type')}"
            )

        resource = event.get("resource", {})
        provider_payment_id = resource.get("supplementary_data", {}).get("related_ids", {}).get(
            "order_id"
        ) or resource.get("id")
        return WebhookEventData(
            event_id=event["id"], event_type=event_type, provider_payment_id=provider_payment_id
        )

    def refund_payment(self, provider_payment_id, *, amount):
        token = self._access_token()
        try:
            response = requests.post(
                f"{_API_BASE}/v2/payments/captures/{provider_payment_id}/refund",
                headers={"Authorization": f"Bearer {token}"},
                json={"amount": {"value": str(amount), "currency_code": "USD"}},
                timeout=10,
            )
        except requests.exceptions.RequestException as exc:
            raise PaymentProviderError(f"PayPal request failed: {exc}") from exc
        if response.status_code not in (200, 201):
            raise PaymentProviderError(f"PayPal refund failed: {response.text}")
        data = response.json()
        status = "succeeded" if data.get("status") == "COMPLETED" else "pending"
        return RefundResult(provider_refund_id=data["id"], status=status)
