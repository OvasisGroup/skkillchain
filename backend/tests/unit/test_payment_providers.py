import hashlib
import hmac
import json
import time

import pytest

from apps.commerce.providers.base import PaymentProviderError, WebhookVerificationError
from apps.commerce.providers.flutterwave import FlutterwavePaymentProvider
from apps.commerce.providers.mpesa import MpesaPaymentProvider
from apps.commerce.providers.paypal import PayPalPaymentProvider
from apps.commerce.providers.paystack import PaystackPaymentProvider
from apps.commerce.providers.registry import get_provider
from apps.commerce.providers.stripe import StripePaymentProvider


class _FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class TestStripeWebhookVerification:
    def test_accepts_genuinely_signed_event(self, settings):
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"
        payload = json.dumps(
            {"id": "evt_1", "type": "payment_intent.succeeded", "data": {"object": {"id": "pi_1"}}}
        )
        timestamp = str(int(time.time()))
        signed_payload = f"{timestamp}.{payload}".encode()
        signature = hmac.new(
            settings.STRIPE_WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256
        ).hexdigest()

        event = StripePaymentProvider().verify_and_parse_webhook(
            payload.encode(), {"Stripe-Signature": f"t={timestamp},v1={signature}"}
        )

        assert event.event_id == "evt_1"
        assert event.event_type == "payment.succeeded"
        assert event.provider_payment_id == "pi_1"

    def test_rejects_wrong_secret(self, settings):
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"
        payload = json.dumps(
            {"id": "evt_1", "type": "payment_intent.succeeded", "data": {"object": {"id": "pi_1"}}}
        )
        timestamp = str(int(time.time()))
        signed_payload = f"{timestamp}.{payload}".encode()
        signature = hmac.new(b"wrong-secret", signed_payload, hashlib.sha256).hexdigest()

        with pytest.raises(WebhookVerificationError):
            StripePaymentProvider().verify_and_parse_webhook(
                payload.encode(), {"Stripe-Signature": f"t={timestamp},v1={signature}"}
            )

    def test_rejects_missing_signature_header(self, settings):
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"
        payload = json.dumps(
            {"id": "evt_1", "type": "payment_intent.succeeded", "data": {"object": {"id": "pi_1"}}}
        )

        with pytest.raises(WebhookVerificationError):
            StripePaymentProvider().verify_and_parse_webhook(payload.encode(), {})

    def test_rejects_stale_timestamp(self, settings):
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"
        payload = json.dumps(
            {"id": "evt_1", "type": "payment_intent.succeeded", "data": {"object": {"id": "pi_1"}}}
        )
        stale_timestamp = str(int(time.time()) - 1000)
        signed_payload = f"{stale_timestamp}.{payload}".encode()
        signature = hmac.new(
            settings.STRIPE_WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256
        ).hexdigest()

        with pytest.raises(WebhookVerificationError):
            StripePaymentProvider().verify_and_parse_webhook(
                payload.encode(), {"Stripe-Signature": f"t={stale_timestamp},v1={signature}"}
            )


class TestPaystackWebhookVerification:
    def test_accepts_genuinely_signed_event(self, settings):
        settings.PAYSTACK_SECRET_KEY = "sk_test_secret"
        payload = json.dumps(
            {"event": "charge.success", "data": {"id": 123, "reference": "order-1"}}
        ).encode()
        signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(), payload, hashlib.sha512
        ).hexdigest()

        event = PaystackPaymentProvider().verify_and_parse_webhook(
            payload, {"X-Paystack-Signature": signature}
        )

        assert event.event_type == "payment.succeeded"
        assert event.provider_payment_id == "order-1"

    def test_rejects_tampered_body(self, settings):
        settings.PAYSTACK_SECRET_KEY = "sk_test_secret"
        payload = json.dumps(
            {"event": "charge.success", "data": {"id": 123, "reference": "order-1"}}
        ).encode()
        signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(), payload, hashlib.sha512
        ).hexdigest()
        tampered_payload = json.dumps(
            {"event": "charge.success", "data": {"id": 123, "reference": "order-2"}}
        ).encode()

        with pytest.raises(WebhookVerificationError):
            PaystackPaymentProvider().verify_and_parse_webhook(
                tampered_payload, {"X-Paystack-Signature": signature}
            )


class TestFlutterwaveWebhookVerification:
    def test_accepts_matching_secret_hash(self, settings):
        settings.FLUTTERWAVE_WEBHOOK_SECRET_HASH = "configured-secret"
        payload = json.dumps(
            {"data": {"id": 5, "tx_ref": "order-1", "status": "successful"}}
        ).encode()

        event = FlutterwavePaymentProvider().verify_and_parse_webhook(
            payload, {"Verif-Hash": "configured-secret"}
        )

        assert event.event_type == "payment.succeeded"
        assert event.provider_payment_id == "order-1"

    def test_rejects_wrong_hash(self, settings):
        settings.FLUTTERWAVE_WEBHOOK_SECRET_HASH = "configured-secret"
        payload = json.dumps(
            {"data": {"id": 5, "tx_ref": "order-1", "status": "successful"}}
        ).encode()

        with pytest.raises(WebhookVerificationError):
            FlutterwavePaymentProvider().verify_and_parse_webhook(payload, {"Verif-Hash": "wrong"})

    def test_rejects_missing_hash(self, settings):
        settings.FLUTTERWAVE_WEBHOOK_SECRET_HASH = "configured-secret"
        payload = json.dumps(
            {"data": {"id": 5, "tx_ref": "order-1", "status": "successful"}}
        ).encode()

        with pytest.raises(WebhookVerificationError):
            FlutterwavePaymentProvider().verify_and_parse_webhook(payload, {})


class TestMpesaProvider:
    def test_create_payment_requires_phone_number(self):
        with pytest.raises(PaymentProviderError):
            MpesaPaymentProvider().create_payment(amount=100, currency="KES", order_id="order-1")

    def test_webhook_accepts_matching_callback_secret(self, settings):
        settings.MPESA_CALLBACK_SECRET = "configured-secret"
        payload = json.dumps(
            {"Body": {"stkCallback": {"CheckoutRequestID": "ws_1", "ResultCode": 0}}}
        ).encode()

        event = MpesaPaymentProvider().verify_and_parse_webhook(
            payload, {"X-Callback-Path-Secret": "configured-secret"}
        )

        assert event.event_type == "payment.succeeded"
        assert event.provider_payment_id == "ws_1"

    def test_webhook_nonzero_result_code_is_failure(self, settings):
        settings.MPESA_CALLBACK_SECRET = "configured-secret"
        payload = json.dumps(
            {"Body": {"stkCallback": {"CheckoutRequestID": "ws_1", "ResultCode": 1}}}
        ).encode()

        event = MpesaPaymentProvider().verify_and_parse_webhook(
            payload, {"X-Callback-Path-Secret": "configured-secret"}
        )

        assert event.event_type == "payment.failed"

    def test_webhook_rejects_wrong_secret(self, settings):
        settings.MPESA_CALLBACK_SECRET = "configured-secret"
        payload = json.dumps(
            {"Body": {"stkCallback": {"CheckoutRequestID": "ws_1", "ResultCode": 0}}}
        ).encode()

        with pytest.raises(WebhookVerificationError):
            MpesaPaymentProvider().verify_and_parse_webhook(
                payload, {"X-Callback-Path-Secret": "wrong-secret"}
            )

    def test_refund_not_implemented(self):
        with pytest.raises(PaymentProviderError):
            MpesaPaymentProvider().refund_payment("ws_1", amount=100)


class TestPayPalWebhookVerification:
    """
    PayPal has no local signature check — verification means calling their
    own API, so these tests mock that HTTP call rather than computing a
    real signature (same pattern as the M1 Facebook OAuth adapter tests).
    """

    def test_accepts_when_provider_confirms_success(self, monkeypatch):
        monkeypatch.setattr(
            "apps.commerce.providers.paypal.requests.post",
            lambda url, **k: (
                _FakeResponse(200, {"access_token": "tok"})
                if "oauth2/token" in url
                else _FakeResponse(200, {"verification_status": "SUCCESS"})
            ),
        )
        payload = json.dumps(
            {
                "id": "WH-1",
                "event_type": "PAYMENT.CAPTURE.COMPLETED",
                "resource": {
                    "id": "capture-1",
                    "supplementary_data": {"related_ids": {"order_id": "order-1"}},
                },
            }
        ).encode()

        event = PayPalPaymentProvider().verify_and_parse_webhook(payload, {})

        assert event.event_type == "payment.succeeded"
        assert event.provider_payment_id == "order-1"

    def test_rejects_when_provider_reports_failure(self, monkeypatch):
        monkeypatch.setattr(
            "apps.commerce.providers.paypal.requests.post",
            lambda url, **k: (
                _FakeResponse(200, {"access_token": "tok"})
                if "oauth2/token" in url
                else _FakeResponse(200, {"verification_status": "FAILURE"})
            ),
        )
        payload = json.dumps(
            {"id": "WH-1", "event_type": "PAYMENT.CAPTURE.COMPLETED", "resource": {}}
        ).encode()

        with pytest.raises(WebhookVerificationError):
            PayPalPaymentProvider().verify_and_parse_webhook(payload, {})


class TestRegistry:
    def test_all_five_providers_registered(self):
        for code in ["stripe", "paypal", "flutterwave", "paystack", "mpesa"]:
            assert get_provider(code) is not None

    def test_unknown_provider_returns_none(self):
        assert get_provider("amazon-pay") is None
