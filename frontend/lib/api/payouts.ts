import { apiFetch } from "./client";
import type { EarningsAggregate, Payout, Wallet } from "./types";

export function getInstructorWallet(token: string): Promise<Wallet> {
  return apiFetch<Wallet>("/instructor/wallet/", { token, cache: "no-store" });
}

export function listInstructorPayouts(token: string): Promise<Payout[]> {
  return apiFetch<Payout[]>("/instructor/payouts/", { token, cache: "no-store" });
}

export function requestInstructorPayout(token: string): Promise<Payout> {
  return apiFetch<Payout>("/instructor/payout-requests/", { method: "POST", token });
}

export function getInstructorEarnings(token: string): Promise<EarningsAggregate[]> {
  return apiFetch<EarningsAggregate[]>("/analytics/instructor-earnings/", {
    token,
    cache: "no-store",
  });
}
