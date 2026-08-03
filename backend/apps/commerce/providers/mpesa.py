"""
M-Pesa (Safaricom Daraja API) adapter.

Two real differences from the other four providers, both documented here
rather than papered over:

1. STK Push is phone-initiated, not redirect/client-secret based — the
   buyer's phone number is required to start a payment, which none of the
   other providers need. create_payment() requires it via kwargs and
   raises PaymentProviderError with a clear message if it's missing,
   rather than silently accepting an unusable request.

2. Daraja callbacks carry no cryptographic signature at all — Safaricom's
   real security model is IP allowlisting at the network layer (their
   published IP ranges), which this application-level code cannot enforce
   from within Django. As a practical substitute, the callback URL is
   registered with a secret path token (MPESA_CALLBACK_SECRET); the view
   passes that matched URL segment in through the headers dict under
   "X-Callback-Path-Secret" so this adapter can still reject a call that
   doesn't know the secret. This is NOT equivalent to real IP allowlisting
   and production deployments must add that at the load balancer/WAF —
   documented as a known gap, not a guarantee.
"""

import base64
import hmac
import json
from datetime import datetime

import requests
from django.conf import settings

from .base import (
    PaymentInit,
    PaymentProvider,
    PaymentProviderError,
    WebhookEventData,
    WebhookVerificationError,
)

_API_BASES = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}


class MpesaPaymentProvider(PaymentProvider):
    code = "mpesa"

    @property
    def _api_base(self) -> str:
        # Daraja's sandbox and production environments live on entirely
        # different hosts (not just different credentials) — defaults to
        # sandbox so an unset/typo'd MPESA_ENVIRONMENT fails safe rather
        # than accidentally hitting production.
        return _API_BASES.get(settings.MPESA_ENVIRONMENT, _API_BASES["sandbox"])

    def _access_token(self) -> str:
        try:
            response = requests.get(
                f"{self._api_base}/oauth/v1/generate",
                params={"grant_type": "client_credentials"},
                auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
                timeout=10,
            )
        except requests.exceptions.RequestException as exc:
            raise PaymentProviderError(f"M-Pesa auth request failed: {exc}") from exc
        if response.status_code != 200:
            raise PaymentProviderError(f"M-Pesa auth failed: {response.text}")
        return response.json()["access_token"]

    def create_payment(self, *, amount, currency, order_id, phone_number: str | None = None):
        if not phone_number:
            raise PaymentProviderError(
                "M-Pesa STK Push requires the buyer's phone_number — it cannot be initiated "
                "the same way as a redirect/client-secret provider."
            )
        if currency != "KES":
            # Daraja has no notion of currency at all — it only ever moves
            # Kenyan Shillings. Silently sending a USD/etc-denominated
            # amount would charge that many *shillings*, not convert it —
            # reject rather than let that happen.
            raise PaymentProviderError(
                f"M-Pesa only supports KES-denominated orders; this order is in {currency}."
            )
        token = self._access_token()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()
        ).decode()

        try:
            response = requests.post(
                f"{self._api_base}/mpesa/stkpush/v1/processrequest",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "BusinessShortCode": settings.MPESA_SHORTCODE,
                    "Password": password,
                    "Timestamp": timestamp,
                    "TransactionType": "CustomerPayBillOnline",
                    "Amount": int(amount),
                    "PartyA": phone_number,
                    "PartyB": settings.MPESA_SHORTCODE,
                    "PhoneNumber": phone_number,
                    "CallBackURL": settings.MPESA_CALLBACK_URL,
                    "AccountReference": order_id,
                    "TransactionDesc": "SkillChain order",
                },
                timeout=10,
            )
        except requests.exceptions.RequestException as exc:
            raise PaymentProviderError(f"M-Pesa request failed: {exc}") from exc
        if response.status_code != 200:
            raise PaymentProviderError(f"M-Pesa STK push failed: {response.text}")
        data = response.json()
        return PaymentInit(
            provider_payment_id=data["CheckoutRequestID"], client_secret=None, redirect_url=None
        )

    def verify_and_parse_webhook(self, raw_body: bytes, headers: dict) -> WebhookEventData:
        received_secret = headers.get("X-Callback-Path-Secret", "")
        if not received_secret or not hmac.compare_digest(
            received_secret, settings.MPESA_CALLBACK_SECRET
        ):
            raise WebhookVerificationError("M-Pesa callback path secret mismatch.")

        event = json.loads(raw_body)
        callback = event.get("Body", {}).get("stkCallback", {})
        result_code = callback.get("ResultCode")
        if result_code is None:
            raise WebhookVerificationError("M-Pesa callback missing ResultCode.")

        event_type = "payment.succeeded" if result_code == 0 else "payment.failed"
        return WebhookEventData(
            event_id=str(callback["CheckoutRequestID"]),
            event_type=event_type,
            provider_payment_id=str(callback["CheckoutRequestID"]),
        )

    def refund_payment(self, provider_payment_id, *, amount):
        # Daraja's reversal API exists but requires a security credential
        # (RSA-encrypted initiator password) and a separate app-level
        # queue/timeout callback pair beyond what's built here — not
        # implemented; matches the "coding exercise sandbox" pattern of
        # naming a real gap rather than faking success.
        raise PaymentProviderError(
            "M-Pesa reversal is not implemented — requires Daraja's separate "
            "initiator-credential reversal API, not yet built."
        )
