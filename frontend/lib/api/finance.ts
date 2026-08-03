import { apiFetch } from "./client";
import type { Coupon, Promotion, RevenueDailyAggregate } from "./types";

export function getRevenue(token: string): Promise<RevenueDailyAggregate[]> {
  return apiFetch<RevenueDailyAggregate[]>("/analytics/revenue/", { token, cache: "no-store" });
}

export function listCoupons(token: string): Promise<Coupon[]> {
  return apiFetch<Coupon[]>("/admin/coupons/", { token, cache: "no-store" });
}

export function createCoupon(
  body: Pick<Coupon, "code" | "discount_type" | "discount_value"> &
    Partial<Pick<Coupon, "valid_from" | "valid_to" | "usage_limit" | "per_user_limit">>,
  token: string
): Promise<Coupon> {
  return apiFetch<Coupon>("/admin/coupons/", { method: "POST", token, body });
}

export function listPromotions(token: string): Promise<Promotion[]> {
  return apiFetch<Promotion[]>("/admin/promotions/", { token, cache: "no-store" });
}

export function createPromotion(
  body: Pick<Promotion, "name"> & Partial<Omit<Promotion, "id" | "name">>,
  token: string
): Promise<Promotion> {
  return apiFetch<Promotion>("/admin/promotions/", { method: "POST", token, body });
}

export function updatePromotion(
  promotionId: string,
  patch: Partial<Omit<Promotion, "id">>,
  token: string
): Promise<Promotion> {
  return apiFetch<Promotion>(`/admin/promotions/${promotionId}/`, {
    method: "PATCH",
    token,
    body: patch,
  });
}
