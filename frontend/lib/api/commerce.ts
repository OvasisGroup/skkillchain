import { apiFetch } from "./client";
import type { Order, PayResponse, PaymentProviderCode } from "./types";

export function createOrder(
  items: { item_type: "course"; item_id: string }[],
  token: string,
  referralCode?: string
): Promise<Order> {
  return apiFetch<Order>("/checkout/orders/", {
    method: "POST",
    token,
    body: referralCode ? { items, referral_code: referralCode } : { items },
  });
}

// Poll this while a payment is pending — async providers (M-Pesa's STK
// push, in particular) confirm via a provider webhook that lands well after
// the pay response, not synchronously in payOrder()'s return value.
export function getOrder(orderId: string, token: string): Promise<Order> {
  return apiFetch<Order>(`/checkout/orders/${orderId}/`, { token, cache: "no-store" });
}

export function applyCoupon(orderId: string, code: string, token: string): Promise<Order> {
  return apiFetch<Order>(`/checkout/orders/${orderId}/apply-coupon/`, {
    method: "POST",
    token,
    body: { code },
  });
}

export function applyGiftCard(
  orderId: string,
  code: string,
  token: string,
  amount?: string
): Promise<Order> {
  return apiFetch<Order>(`/checkout/orders/${orderId}/apply-gift-card/`, {
    method: "POST",
    token,
    body: amount ? { code, amount } : { code },
  });
}

export function payOrder(
  orderId: string,
  provider: PaymentProviderCode,
  token: string,
  phoneNumber?: string
): Promise<PayResponse> {
  return apiFetch<PayResponse>(`/checkout/orders/${orderId}/pay/`, {
    method: "POST",
    token,
    body: phoneNumber ? { provider, phone_number: phoneNumber } : { provider },
  });
}
