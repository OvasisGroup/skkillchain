"use client";

import { AlertCircle } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { AuthCard, AuthDivider, authInputClass, authLabelClass } from "@/components/AuthCard";
import { GoogleSignInButton } from "@/components/GoogleSignInButton";
import { ApiError } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/AuthContext";
import { primaryDashboardPath, safeRedirectPath } from "@/lib/auth/roles";

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, completeMfaLogin, loginWithGoogle } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleGoogleToken(idToken: string) {
    setError(null);
    setIsSubmitting(true);
    try {
      const user = await loginWithGoogle(idToken);
      router.push(safeRedirectPath(searchParams.get("next"), primaryDashboardPath(user)));
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message_ : "Something went wrong. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCredentialsSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const result = await login(email, password);
      if ("mfaToken" in result) {
        setMfaToken(result.mfaToken);
      } else {
        router.push(safeRedirectPath(searchParams.get("next"), primaryDashboardPath(result.user)));
      }
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message_ : "Something went wrong. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleMfaSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!mfaToken) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const user = await completeMfaLogin(mfaToken, code);
      router.push(safeRedirectPath(searchParams.get("next"), primaryDashboardPath(user)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Invalid code. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (mfaToken) {
    return (
      <AuthCard
        title="Two-factor verification"
        subtitle="Enter the 6-digit code from your authenticator app."
      >
        <form onSubmit={handleMfaSubmit} className="space-y-5">
          {error && (
            <div className="flex items-start gap-2 rounded-lg bg-red-500/10 p-3 text-sm text-red-400">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-none" />
              <span>{error}</span>
            </div>
          )}
          <input
            type="text"
            inputMode="numeric"
            required
            minLength={6}
            maxLength={6}
            autoFocus
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className={`${authInputClass} text-center text-lg tracking-[0.5em]`}
            placeholder="000000"
          />
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-full bg-teal-400 px-6 py-3 text-sm font-semibold text-emerald-950 shadow-sm shadow-teal-500/20 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Verifying…" : "Verify"}
          </button>
        </form>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title="Welcome back"
      subtitle={
        <>
          New to SkillChain?{" "}
          <Link
            href={`/register${searchParams.get("next") ? `?next=${encodeURIComponent(searchParams.get("next")!)}` : ""}`}
            className="font-medium text-teal-400 hover:text-teal-300"
          >
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={handleCredentialsSubmit} className="space-y-5">
        {error && (
          <div className="flex items-start gap-2 rounded-lg bg-red-500/10 p-3 text-sm text-red-400">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-none" />
            <span>{error}</span>
          </div>
        )}

        <div>
          <label htmlFor="email" className={authLabelClass}>
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={authInputClass}
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label htmlFor="password" className={authLabelClass}>
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={authInputClass}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-full bg-teal-400 px-6 py-3 text-sm font-semibold text-emerald-950 shadow-sm shadow-teal-500/20 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Logging in…" : "Log in"}
        </button>
      </form>

      <AuthDivider label="or" />
      <GoogleSignInButton onToken={handleGoogleToken} onError={setError} />
    </AuthCard>
  );
}
