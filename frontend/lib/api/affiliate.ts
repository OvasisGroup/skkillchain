import { apiFetch } from "./client";
import type { AffiliateAccount, AffiliateCommission, AffiliateReferral, Payout, Wallet } from "./types";

export function registerAffiliate(token: string): Promise<AffiliateAccount> {
  return apiFetch<AffiliateAccount>("/affiliate/register/", { method: "POST", token });
}

export function getAffiliateMe(token: string): Promise<AffiliateAccount> {
  return apiFetch<AffiliateAccount>("/affiliate/me/", { token, cache: "no-store" });
}

export function listReferrals(token: string): Promise<AffiliateReferral[]> {
  return apiFetch<AffiliateReferral[]>("/affiliate/referrals/", { token, cache: "no-store" });
}

export function listCommissions(token: string): Promise<AffiliateCommission[]> {
  return apiFetch<AffiliateCommission[]>("/affiliate/commissions/", { token, cache: "no-store" });
}

export function getAffiliateWallet(token: string): Promise<Wallet> {
  return apiFetch<Wallet>("/affiliate/wallet/", { token, cache: "no-store" });
}

export function requestAffiliatePayout(token: string): Promise<Payout> {
  return apiFetch<Payout>("/affiliate/payout-requests/", { method: "POST", token });
}
