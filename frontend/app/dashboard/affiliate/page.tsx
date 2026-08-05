"use client";

import { DollarSign, Link2, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { Panel } from "@/components/dashboard/Panel";
import { StatCard } from "@/components/dashboard/StatCard";
import {
  getAffiliateMe,
  getAffiliateWallet,
  listCommissions,
  listReferrals,
  registerAffiliate,
  requestAffiliatePayout,
} from "@/lib/api/affiliate";
import { ApiError } from "@/lib/api/client";
import type { AffiliateAccount, AffiliateCommission, AffiliateReferral, Wallet } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";
import { Reveal } from "@/components/animation/Reveal";

export default function AffiliateDashboardPage() {
  const { accessToken } = useAuth();
  const [account, setAccount] = useState<AffiliateAccount | null>(null);
  const [referrals, setReferrals] = useState<AffiliateReferral[]>([]);
  const [commissions, setCommissions] = useState<AffiliateCommission[]>([]);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [loading, setLoading] = useState(true);
  const [registering, setRegistering] = useState(false);
  const [payoutBusy, setPayoutBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;

    getAffiliateMe(accessToken)
      .then(async (acc) => {
        if (cancelled) return;
        setAccount(acc);
        const [referralsData, commissionsData, walletData] = await Promise.all([
          listReferrals(accessToken),
          listCommissions(accessToken),
          getAffiliateWallet(accessToken),
        ]);
        if (cancelled) return;
        setReferrals(referralsData);
        setCommissions(commissionsData);
        setWallet(walletData);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 403) {
          setAccount(null);
        } else {
          setError(err instanceof ApiError ? err.message_ : "Couldn't load your affiliate account.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function handleRegister() {
    if (!accessToken) return;
    setRegistering(true);
    try {
      const acc = await registerAffiliate(accessToken);
      setAccount(acc);
      const [referralsData, commissionsData, walletData] = await Promise.all([
        listReferrals(accessToken),
        listCommissions(accessToken),
        getAffiliateWallet(accessToken),
      ]);
      setReferrals(referralsData);
      setCommissions(commissionsData);
      setWallet(walletData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't register as an affiliate.");
    } finally {
      setRegistering(false);
    }
  }

  async function handleRequestPayout() {
    if (!accessToken) return;
    setPayoutBusy(true);
    try {
      await requestAffiliatePayout(accessToken);
      setWallet((prev) => (prev ? { ...prev, balance_amount: "0.00" } : prev));
      const commissionsData = await listCommissions(accessToken);
      setCommissions(commissionsData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't request a payout.");
    } finally {
      setPayoutBusy(false);
    }
  }

  if (error) return <ErrorState message={error} />;
  if (loading) return <LoadingState label="Loading your affiliate dashboard…" />;

  if (!account) {
    return (
      <div className="rounded-2xl border border-border bg-surface p-8 text-center">
        <Link2 className="mx-auto h-8 w-8 text-teal-400" />
        <h1 className="mt-4 text-xl font-semibold text-foreground">Become an affiliate</h1>
        <p className="mt-2 text-sm text-foreground/60">
          Earn a commission for every student you refer to SkillChain.
        </p>
        <button
          type="button"
          onClick={handleRegister}
          disabled={registering}
          className="mt-6 rounded-full bg-teal-400 px-6 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {registering ? "Registering…" : "Register as an affiliate"}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader title="Affiliate" />

      <Reveal className="grid grid-cols-2 gap-4 sm:grid-cols-4" stagger={0.08}>
        <StatCard label="Referral code" value={account.referral_code} icon={Link2} />
        <StatCard label="Commission rate" value={`${account.commission_rate}%`} icon={DollarSign} />
        <StatCard label="Referrals" value={String(referrals.length)} icon={Users} />
        <StatCard
          label="Wallet balance"
          value={wallet ? `${wallet.currency} ${wallet.balance_amount}` : "—"}
          icon={DollarSign}
        />
      </Reveal>

      <div className="flex flex-wrap items-center gap-4 rounded-2xl border border-border bg-surface p-5">
        <p className="text-sm text-foreground/70">
          Available balance:{" "}
          <span className="font-semibold text-foreground">
            {wallet ? `${wallet.currency} ${wallet.balance_amount}` : "—"}
          </span>
        </p>
        <button
          type="button"
          onClick={handleRequestPayout}
          disabled={payoutBusy || !wallet || Number(wallet.balance_amount) <= 0}
          className="rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {payoutBusy ? "Requesting…" : "Request payout"}
        </button>
      </div>

      <Panel title="Referrals">
        <DataTable
          rows={referrals}
          getRowKey={(r) => r.id}
          emptyMessage="No referrals yet — share your referral code to get started."
          columns={[
            { header: "Referred user", cell: (r) => r.referred_user_email },
            {
              header: "Status",
              cell: (r) => <span className="capitalize">{r.status}</span>,
            },
            { header: "Date", cell: (r) => new Date(r.created_at).toLocaleDateString() },
          ]}
        />
      </Panel>

      <Panel title="Commissions">
        <DataTable
          rows={commissions}
          getRowKey={(c) => c.id}
          emptyMessage="No commissions earned yet."
          columns={[
            { header: "Amount", cell: (c) => c.commission_amount },
            {
              header: "Payout status",
              cell: (c) => <span className="capitalize">{c.payout_status}</span>,
            },
            { header: "Date", cell: (c) => new Date(c.created_at).toLocaleDateString() },
          ]}
        />
      </Panel>
    </div>
  );
}
