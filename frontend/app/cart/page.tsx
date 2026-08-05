"use client";

import { Award, PlayCircle, ShoppingCart, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { ApiError } from "@/lib/api/client";
import { applyCoupon, applyGiftCard, createOrder, getOrder, payOrder } from "@/lib/api/commerce";
import { listMyCourses } from "@/lib/api/enrollments";
import type { Enrollment, Order, PayResponse, PaymentProviderCode } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";
import { useCart } from "@/lib/cart/CartContext";
import { Reveal } from "@/components/animation/Reveal";

const STATUS_STYLES: Record<string, string> = {
  active: "bg-teal-400/10 text-teal-400",
  completed: "bg-emerald-500/10 text-emerald-400",
};

const PROVIDERS: { code: PaymentProviderCode; label: string }[] = [
  { code: "stripe", label: "Stripe" },
  { code: "paypal", label: "PayPal" },
  { code: "flutterwave", label: "Flutterwave" },
  { code: "paystack", label: "Paystack" },
  { code: "mpesa", label: "M-Pesa" },
];

type Tab = "cart" | "my-courses";
type CheckoutStep = "idle" | "order-created" | "paid";

export default function CartPage() {
  const [tab, setTab] = useState<Tab>("cart");

  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <Reveal className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">My learning</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Cart
        </h1>
        <p className="mt-3 text-lg text-foreground/60">
          Review courses you&apos;re about to buy, or jump into ones you already own.
        </p>
      </Reveal>

      <div className="mt-8 flex gap-2 border-b border-border">
        <button
          type="button"
          onClick={() => setTab("cart")}
          className={`border-b-2 px-1 pb-3 text-sm font-medium transition-colors ${
            tab === "cart"
              ? "border-teal-400 text-foreground"
              : "border-transparent text-foreground/50 hover:text-foreground"
          }`}
        >
          Cart
        </button>
        <button
          type="button"
          onClick={() => setTab("my-courses")}
          className={`border-b-2 px-1 pb-3 text-sm font-medium transition-colors ${
            tab === "my-courses"
              ? "border-teal-400 text-foreground"
              : "border-transparent text-foreground/50 hover:text-foreground"
          }`}
        >
          My courses
        </button>
      </div>

      <div className="mt-10">
        {tab === "cart" ? <CartTab onPurchased={() => setTab("my-courses")} /> : <MyCoursesTab />}
      </div>
    </div>
  );
}

function CartTab({ onPurchased }: { onPurchased: () => void }) {
  const { accessToken } = useAuth();
  const { items, removeItem, clear } = useCart();
  const [step, setStep] = useState<CheckoutStep>("idle");
  const [order, setOrder] = useState<Order | null>(null);
  const [provider, setProvider] = useState<PaymentProviderCode>("stripe");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [payResult, setPayResult] = useState<PayResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [referralCode, setReferralCode] = useState("");
  const [couponCode, setCouponCode] = useState("");
  const [giftCardCode, setGiftCardCode] = useState("");
  const [applyBusy, setApplyBusy] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [pollTimedOut, setPollTimedOut] = useState(false);

  // Async providers (M-Pesa's STK push, in particular) confirm via webhook
  // well after payOrder() returns "pending" — poll order status until the
  // webhook lands, the payment fails, or we give up.
  useEffect(() => {
    if (!accessToken || !order || payResult?.payment.status !== "pending" || pollTimedOut) return;
    let cancelled = false;
    let attempts = 0;
    const maxAttempts = 40; // ~2 minutes at 3s
    const orderId = order.id;
    const intervalId = setInterval(async () => {
      attempts += 1;
      try {
        const latest = await getOrder(orderId, accessToken);
        if (cancelled) return;
        setOrder(latest);
        if (latest.status === "paid") {
          clearInterval(intervalId);
          clear();
          setStep("paid");
        } else if (latest.latest_payment?.status === "failed") {
          clearInterval(intervalId);
          setError("Payment failed. You can try again with a different method.");
        } else if (attempts >= maxAttempts) {
          clearInterval(intervalId);
          setPollTimedOut(true);
        }
      } catch {
        if (!cancelled && attempts >= maxAttempts) {
          clearInterval(intervalId);
          setPollTimedOut(true);
        }
      }
    }, 3000);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
    // Re-runs only when a fresh pay attempt starts (order id or payment
    // status changes) — polling ticks themselves update `order`, not this
    // dependency list, so they don't restart the interval.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, order?.id, payResult?.payment.status, pollTimedOut]);

  async function handleCheckout() {
    if (!accessToken || items.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      const created = await createOrder(
        items.map((course) => ({ item_type: "course" as const, item_id: course.id })),
        accessToken,
        referralCode.trim() || undefined
      );
      setOrder(created);
      setStep("order-created");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't start checkout.");
    } finally {
      setBusy(false);
    }
  }

  async function handleApplyCoupon() {
    if (!accessToken || !order || !couponCode.trim()) return;
    setApplyBusy(true);
    setApplyError(null);
    try {
      const updated = await applyCoupon(order.id, couponCode.trim(), accessToken);
      setOrder(updated);
      setCouponCode("");
    } catch (err) {
      setApplyError(err instanceof ApiError ? err.message_ : "Couldn't apply this coupon.");
    } finally {
      setApplyBusy(false);
    }
  }

  async function handleApplyGiftCard() {
    if (!accessToken || !order || !giftCardCode.trim()) return;
    setApplyBusy(true);
    setApplyError(null);
    try {
      const updated = await applyGiftCard(order.id, giftCardCode.trim(), accessToken);
      setOrder(updated);
      setGiftCardCode("");
    } catch (err) {
      setApplyError(err instanceof ApiError ? err.message_ : "Couldn't apply this gift card.");
    } finally {
      setApplyBusy(false);
    }
  }

  async function handlePay() {
    if (!accessToken || !order) return;
    setBusy(true);
    setError(null);
    setPollTimedOut(false);
    try {
      const result = await payOrder(
        order.id,
        provider,
        accessToken,
        provider === "mpesa" ? phoneNumber : undefined
      );
      setPayResult(result);
      if (result.payment.status === "succeeded") {
        clear();
        setStep("paid");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't start payment.");
    } finally {
      setBusy(false);
    }
  }

  if (step === "paid") {
    return (
      <div className="rounded-2xl border border-border bg-surface p-8 text-center">
        <Award className="mx-auto h-8 w-8 text-emerald-400" />
        <h2 className="mt-4 text-xl font-semibold text-foreground">Purchase complete</h2>
        <p className="mt-2 text-sm text-foreground/60">
          Your order is paid. The courses are now available under My courses.
        </p>
        <button
          type="button"
          onClick={onPurchased}
          className="mt-6 rounded-full bg-teal-400 px-6 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90"
        >
          Go to my courses
        </button>
      </div>
    );
  }

  if (items.length === 0 && step === "idle") {
    return (
      <div className="flex flex-col items-center rounded-2xl border border-dashed border-border-strong py-20 text-center">
        <ShoppingCart className="h-10 w-10 text-foreground/30" />
        <p className="mt-4 text-sm text-foreground/50">Your cart is empty.</p>
        <Link href="/courses" className="mt-4 text-sm font-medium text-teal-400 hover:underline">
          Browse courses
        </Link>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
      <Reveal className="space-y-3 lg:col-span-2" stagger={0.08}>
        {items.map((course) => (
          <div
            key={course.id}
            className="flex items-center justify-between gap-4 rounded-xl border border-border bg-surface p-4"
          >
            <div className="min-w-0">
              <Link
                href={`/courses/${course.id}`}
                className="truncate text-sm font-semibold text-foreground hover:text-teal-400"
              >
                {course.title}
              </Link>
              <p className="mt-1 text-xs text-foreground/50">{course.instructor.email}</p>
            </div>
            <div className="flex flex-none items-center gap-4">
              <span className="text-sm font-semibold text-foreground">
                {course.price_amount === "0.00" ? "Free" : `${course.currency} ${course.price_amount}`}
              </span>
              {step === "idle" && (
                <button
                  type="button"
                  onClick={() => removeItem(course.id)}
                  aria-label="Remove from cart"
                  className="rounded-full p-1.5 text-foreground/50 transition-colors hover:bg-rose-500/10 hover:text-rose-400"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        ))}
      </Reveal>

      <div className="rounded-2xl border border-border bg-surface p-6">
        {step === "idle" && (
          <>
            <p className="text-sm text-foreground/60">
              {items.length} course{items.length === 1 ? "" : "s"} in cart
            </p>
            <p className="mt-2 text-xs text-foreground/40">
              Final price is calculated at checkout from current catalog prices.
            </p>

            <label className="mt-5 block">
              <span className="text-sm font-medium text-foreground/80">
                Referral code <span className="text-foreground/40">(optional)</span>
              </span>
              <input
                value={referralCode}
                onChange={(e) => setReferralCode(e.target.value)}
                placeholder="e.g. 9F3C1A2B"
                className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
              />
            </label>

            <button
              type="button"
              onClick={handleCheckout}
              disabled={busy}
              className="mt-5 w-full rounded-full bg-teal-400 px-5 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy ? "Starting checkout…" : "Proceed to checkout"}
            </button>
          </>
        )}

        {step === "order-created" && order && (
          <>
            <p className="text-sm font-semibold text-foreground">Order summary</p>
            <div className="mt-2 space-y-1 text-sm">
              <div className="flex items-center justify-between text-foreground/70">
                <span>Subtotal</span>
                <span>
                  {order.currency} {order.subtotal_amount}
                </span>
              </div>
              {Number(order.discount_amount) > 0 && (
                <div className="flex items-center justify-between text-emerald-400">
                  <span>Discount</span>
                  <span>
                    −{order.currency} {order.discount_amount}
                  </span>
                </div>
              )}
              {Number(order.gift_card_amount) > 0 && (
                <div className="flex items-center justify-between text-emerald-400">
                  <span>Gift card</span>
                  <span>
                    −{order.currency} {order.gift_card_amount}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between border-t border-border pt-1.5 font-semibold text-foreground">
                <span>Total</span>
                <span>
                  {order.currency} {order.total_amount}
                </span>
              </div>
            </div>

            <div className="mt-5 space-y-3 border-t border-border pt-5">
              <label className="block">
                <span className="text-sm font-medium text-foreground/80">Coupon code</span>
                <div className="mt-1.5 flex gap-2">
                  <input
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value)}
                    placeholder="e.g. WELCOME10"
                    className="w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
                  />
                  <button
                    type="button"
                    onClick={handleApplyCoupon}
                    disabled={applyBusy || !couponCode.trim()}
                    className="flex-none rounded-lg border border-border-strong px-3 py-2 text-sm font-medium text-foreground/80 transition-colors hover:bg-surface-hover disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Apply
                  </button>
                </div>
              </label>

              <label className="block">
                <span className="text-sm font-medium text-foreground/80">Gift card code</span>
                <div className="mt-1.5 flex gap-2">
                  <input
                    value={giftCardCode}
                    onChange={(e) => setGiftCardCode(e.target.value)}
                    placeholder="e.g. GIFT-ABC123"
                    className="w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
                  />
                  <button
                    type="button"
                    onClick={handleApplyGiftCard}
                    disabled={applyBusy || !giftCardCode.trim()}
                    className="flex-none rounded-lg border border-border-strong px-3 py-2 text-sm font-medium text-foreground/80 transition-colors hover:bg-surface-hover disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Apply
                  </button>
                </div>
              </label>

              {applyError && <p className="text-sm text-rose-400">{applyError}</p>}
            </div>

            <label className="mt-5 block">
              <span className="text-sm font-medium text-foreground/80">Payment method</span>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value as PaymentProviderCode)}
                className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
              >
                {PROVIDERS.map((p) => (
                  <option key={p.code} value={p.code}>
                    {p.label}
                  </option>
                ))}
              </select>
            </label>

            {provider === "mpesa" && (
              <label className="mt-3 block">
                <span className="text-sm font-medium text-foreground/80">M-Pesa phone number</span>
                <input
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="2547XXXXXXXX"
                  className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
                />
              </label>
            )}

            <button
              type="button"
              onClick={handlePay}
              disabled={busy}
              className="mt-5 w-full rounded-full bg-teal-400 px-5 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy ? "Processing…" : `Pay ${order.currency} ${order.total_amount}`}
            </button>

            {payResult && payResult.payment.status !== "succeeded" && (
              <div className="mt-4 rounded-lg border border-border-strong bg-background p-3 text-xs text-foreground/70">
                <p>Payment status: {order.latest_payment?.status ?? payResult.payment.status}</p>
                {payResult.redirect_url && (
                  <a
                    href={payResult.redirect_url}
                    className="mt-2 block text-teal-400 hover:underline"
                  >
                    Continue to {provider} to finish paying
                  </a>
                )}
                {payResult.client_secret && !payResult.redirect_url && (
                  <p className="mt-2">
                    The provider returned a client secret for its own SDK to confirm — this build
                    doesn&apos;t embed that SDK, so payment can&apos;t be finished here.
                  </p>
                )}
                {provider === "mpesa" &&
                  !payResult.redirect_url &&
                  !payResult.client_secret &&
                  order.latest_payment?.status === "pending" &&
                  !pollTimedOut && (
                    <p className="mt-2">
                      Enter your M-Pesa PIN on your phone to approve the STK push. This page will
                      update automatically once it&apos;s confirmed.
                    </p>
                  )}
                {pollTimedOut && (
                  <div className="mt-2">
                    <p>
                      Still waiting on confirmation. If you already approved this on your phone,
                      it can take a little longer to reflect here.
                    </p>
                    <button
                      type="button"
                      onClick={() => setPollTimedOut(false)}
                      className="mt-2 rounded-lg border border-border-strong px-3 py-1.5 text-xs font-medium text-foreground/80 transition-colors hover:bg-surface-hover"
                    >
                      Check again
                    </button>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {error && <p className="mt-4 text-sm text-rose-400">{error}</p>}
      </div>
    </div>
  );
}

function MyCoursesTab() {
  const { accessToken } = useAuth();
  const [enrollments, setEnrollments] = useState<Enrollment[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listMyCourses(accessToken)
      .then((page) => {
        if (!cancelled) setEnrollments(page.results);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof ApiError ? err.message_ : "Couldn't load your courses.");
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  if (error) return <ErrorState message={error} />;
  if (!enrollments) return <LoadingState label="Loading your courses…" />;

  if (enrollments.length === 0) {
    return (
      <div className="flex flex-col items-center rounded-2xl border border-dashed border-border-strong py-20 text-center">
        <PlayCircle className="h-10 w-10 text-foreground/30" />
        <p className="mt-4 text-sm text-foreground/50">You haven&apos;t purchased any courses yet.</p>
        <Link href="/courses" className="mt-4 text-sm font-medium text-teal-400 hover:underline">
          Browse courses
        </Link>
      </div>
    );
  }

  return (
    <Reveal className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" stagger={0.08}>
      {enrollments.map((enrollment) => (
        <Link
          key={enrollment.id}
          href={`/courses/${enrollment.course.id}`}
          className="group flex flex-col rounded-2xl border border-border bg-surface p-5 transition-colors hover:border-teal-400/50 hover:bg-surface-hover"
        >
          <div className="flex items-center gap-2">
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[enrollment.status] ?? ""}`}
            >
              {enrollment.status}
            </span>
            {enrollment.status === "completed" && <Award className="h-4 w-4 text-emerald-400" />}
          </div>
          <h3 className="mt-3 flex-1 text-base font-semibold text-foreground group-hover:text-teal-600 dark:group-hover:text-teal-300">
            {enrollment.course.title}
          </h3>
          <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
            <span className="text-xs text-foreground/50">
              Enrolled {new Date(enrollment.enrolled_at).toLocaleDateString()}
            </span>
            <span className="flex items-center gap-1 text-sm font-medium text-teal-400">
              <PlayCircle className="h-4 w-4" />
              Continue
            </span>
          </div>
        </Link>
      ))}
    </Reveal>
  );
}
