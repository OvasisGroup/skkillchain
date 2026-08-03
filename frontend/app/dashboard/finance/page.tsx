"use client";

import { DollarSign, Percent, Megaphone } from "lucide-react";
import { useEffect, useState } from "react";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { Panel } from "@/components/dashboard/Panel";
import { StatCard } from "@/components/dashboard/StatCard";
import { ApiError } from "@/lib/api/client";
import {
  createCoupon,
  createPromotion,
  getRevenue,
  listCoupons,
  listPromotions,
  updatePromotion,
} from "@/lib/api/finance";
import type { Coupon, Promotion, RevenueDailyAggregate } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

function CreateCouponForm({ onCreated }: { onCreated: (coupon: Coupon) => void }) {
  const { accessToken } = useAuth();
  const [code, setCode] = useState("");
  const [discountType, setDiscountType] = useState<"percent" | "fixed">("percent");
  const [discountValue, setDiscountValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken || !code || !discountValue) return;
    setSaving(true);
    setError(null);
    try {
      const coupon = await createCoupon(
        { code, discount_type: discountType, discount_value: discountValue },
        accessToken
      );
      onCreated(coupon);
      setCode("");
      setDiscountValue("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't create this coupon.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2 rounded-xl border border-border bg-surface p-4">
      <div>
        <label className="block text-xs font-medium text-foreground/60">Code</label>
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          className="mt-1 w-32 rounded-lg border border-border-strong bg-surface px-2 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-foreground/60">Type</label>
        <select
          value={discountType}
          onChange={(e) => setDiscountType(e.target.value as "percent" | "fixed")}
          className="mt-1 rounded-lg border border-border-strong bg-surface px-2 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
        >
          <option value="percent">Percent</option>
          <option value="fixed">Fixed amount</option>
        </select>
      </div>
      <div>
        <label className="block text-xs font-medium text-foreground/60">Value</label>
        <input
          type="number"
          value={discountValue}
          onChange={(e) => setDiscountValue(e.target.value)}
          className="mt-1 w-24 rounded-lg border border-border-strong bg-surface px-2 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
        />
      </div>
      <button
        type="submit"
        disabled={saving || !code || !discountValue}
        className="rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {saving ? "Creating…" : "Create coupon"}
      </button>
      {error && <p className="w-full text-xs text-rose-400">{error}</p>}
    </form>
  );
}

function CreatePromotionForm({ onCreated }: { onCreated: (promotion: Promotion) => void }) {
  const { accessToken } = useAuth();
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken || !name) return;
    setSaving(true);
    setError(null);
    try {
      const promotion = await createPromotion({ name }, accessToken);
      onCreated(promotion);
      setName("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't create this promotion.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2 rounded-xl border border-border bg-surface p-4">
      <div>
        <label className="block text-xs font-medium text-foreground/60">Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-1 w-56 rounded-lg border border-border-strong bg-surface px-2 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
        />
      </div>
      <button
        type="submit"
        disabled={saving || !name}
        className="rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {saving ? "Creating…" : "Create promotion"}
      </button>
      {error && <p className="w-full text-xs text-rose-400">{error}</p>}
    </form>
  );
}

export default function FinanceDashboardPage() {
  const { accessToken } = useAuth();
  const [revenue, setRevenue] = useState<RevenueDailyAggregate[] | null>(null);
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [promotions, setPromotions] = useState<Promotion[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyPromotionId, setBusyPromotionId] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    Promise.all([getRevenue(accessToken), listCoupons(accessToken), listPromotions(accessToken)])
      .then(([revenueData, couponsData, promotionsData]) => {
        if (cancelled) return;
        setRevenue(revenueData);
        setCoupons(couponsData);
        setPromotions(promotionsData);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message_ : "Couldn't load finance data.");
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function handlePromotionStatus(promotionId: string, status: Promotion["status"]) {
    if (!accessToken) return;
    setBusyPromotionId(promotionId);
    try {
      const updated = await updatePromotion(promotionId, { status }, accessToken);
      setPromotions((prev) => prev.map((p) => (p.id === promotionId ? updated : p)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't update this promotion.");
    } finally {
      setBusyPromotionId(null);
    }
  }

  if (error) return <ErrorState message={error} />;
  if (!revenue) return <LoadingState label="Loading finance data…" />;

  const totalGross = revenue.reduce((sum, r) => sum + Number(r.gross_amount), 0);
  const totalNet = revenue.reduce((sum, r) => sum + Number(r.net_amount), 0);

  return (
    <div className="space-y-8">
      <PageHeader title="Finance" />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Gross revenue" value={totalGross.toFixed(2)} icon={DollarSign} />
        <StatCard label="Net revenue" value={totalNet.toFixed(2)} icon={DollarSign} />
        <StatCard label="Coupons" value={String(coupons.length)} icon={Percent} />
        <StatCard label="Promotions" value={String(promotions.length)} icon={Megaphone} />
      </div>

      <Panel title="Revenue">
        <DataTable
          rows={revenue}
          getRowKey={(r) => `${r.period_start}-${r.period_end}`}
          emptyMessage="No revenue recorded yet."
          columns={[
            { header: "Period", cell: (r) => `${r.period_start} – ${r.period_end}` },
            { header: "Gross", cell: (r) => `${r.currency} ${r.gross_amount}` },
            { header: "Net", cell: (r) => `${r.currency} ${r.net_amount}` },
          ]}
        />
      </Panel>

      <Panel title="Coupons">
        <div className="space-y-3">
          <CreateCouponForm onCreated={(c) => setCoupons((prev) => [c, ...prev])} />
          <DataTable
            rows={coupons}
            getRowKey={(c) => c.id}
            emptyMessage="No coupons yet."
            columns={[
              { header: "Code", cell: (c) => c.code },
              {
                header: "Discount",
                cell: (c) =>
                  c.discount_type === "percent" ? `${c.discount_value}%` : `$${c.discount_value}`,
              },
              { header: "Usage limit", cell: (c) => c.usage_limit ?? "Unlimited" },
            ]}
          />
        </div>
      </Panel>

      <Panel title="Promotions">
        <div className="space-y-3">
          <CreatePromotionForm onCreated={(p) => setPromotions((prev) => [p, ...prev])} />
          <DataTable
            rows={promotions}
            getRowKey={(p) => p.id}
            emptyMessage="No promotions yet."
            columns={[
              { header: "Name", cell: (p) => p.name },
              {
                header: "Status",
                cell: (p) => (
                  <select
                    value={p.status}
                    disabled={busyPromotionId === p.id}
                    onChange={(e) => handlePromotionStatus(p.id, e.target.value as Promotion["status"])}
                    className="rounded-full border-0 bg-teal-400/10 px-2.5 py-0.5 text-xs font-medium capitalize text-teal-400"
                  >
                    <option value="draft">Draft</option>
                    <option value="active">Active</option>
                    <option value="ended">Ended</option>
                  </select>
                ),
              },
            ]}
          />
        </div>
      </Panel>
    </div>
  );
}
