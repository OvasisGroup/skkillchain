from .base import PaymentProvider
from .flutterwave import FlutterwavePaymentProvider
from .mpesa import MpesaPaymentProvider
from .paypal import PayPalPaymentProvider
from .paystack import PaystackPaymentProvider
from .stripe import StripePaymentProvider

_PROVIDERS: dict[str, type[PaymentProvider]] = {
    StripePaymentProvider.code: StripePaymentProvider,
    PayPalPaymentProvider.code: PayPalPaymentProvider,
    FlutterwavePaymentProvider.code: FlutterwavePaymentProvider,
    PaystackPaymentProvider.code: PaystackPaymentProvider,
    MpesaPaymentProvider.code: MpesaPaymentProvider,
}


def get_provider(code: str) -> PaymentProvider | None:
    provider_class = _PROVIDERS.get(code)
    if provider_class is None:
        return None
    return provider_class()
