"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import * as authApi from "@/lib/api/auth";
import { setRefreshHandler } from "@/lib/api/client";
import { isMfaChallenge } from "@/lib/api/types";
import type { Me } from "@/lib/api/types";
import { SessionExpiredModal } from "@/components/auth/SessionExpiredModal";

const STORAGE_KEY = "skillchain.tokens";

interface StoredTokens {
  access: string;
  refresh: string;
}

interface AuthContextValue {
  user: Me | null;
  accessToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  /** Resolves to the logged-in user, or the pending mfaToken if a code is required. */
  login: (email: string, password: string) => Promise<{ user: Me } | { mfaToken: string }>;
  completeMfaLogin: (mfaToken: string, code: string) => Promise<Me>;
  register: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<Me>;
  logout: () => Promise<void>;
  setUser: (user: Me) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredTokens(): StoredTokens | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredTokens;
  } catch {
    return null;
  }
}

function storeTokens(tokens: StoredTokens | null) {
  if (typeof window === "undefined") return;
  if (tokens) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
  } else {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [tokens, setTokens] = useState<StoredTokens | null>(() => readStoredTokens());
  const [user, setUser] = useState<Me | null>(null);
  const [isLoading, setIsLoading] = useState(() => readStoredTokens() !== null);

  // apiFetch calls this on a 401 from inside lib/api/*.ts, which have no
  // access to React state — the ref keeps it reading the *current* refresh
  // token across rotations without re-registering the handler each render.
  const tokensRef = useRef(tokens);
  useEffect(() => {
    tokensRef.current = tokens;
  }, [tokens]);

  const [sessionExpired, setSessionExpired] = useState(false);
  const [continuing, setContinuing] = useState(false);
  // Holds the resolver for the in-flight refresh promise apiFetch is
  // awaiting — set when the modal opens, called once the user picks
  // Continue or Cancel. client.ts's own dedup means at most one of these
  // is ever pending at a time, so a single ref (not a queue) is enough.
  const pendingResolveRef = useRef<((token: string | null) => void) | null>(null);

  const performRefresh = useCallback(async (): Promise<string | null> => {
    const current = tokensRef.current;
    if (!current) return null;
    try {
      const next = await authApi.refresh(current.refresh);
      storeTokens(next);
      setTokens(next);
      return next.access;
    } catch {
      storeTokens(null);
      setTokens(null);
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    setRefreshHandler(() => {
      if (!tokensRef.current) return Promise.resolve(null);
      return new Promise<string | null>((resolve) => {
        pendingResolveRef.current = resolve;
        setSessionExpired(true);
      });
    });
    return () => setRefreshHandler(null);
  }, []);

  const handleContinue = useCallback(async () => {
    const resolve = pendingResolveRef.current;
    pendingResolveRef.current = null;
    setContinuing(true);
    const newToken = await performRefresh();
    setContinuing(false);
    setSessionExpired(false);
    resolve?.(newToken);
  }, [performRefresh]);

  const handleCancel = useCallback(() => {
    const resolve = pendingResolveRef.current;
    pendingResolveRef.current = null;
    setSessionExpired(false);
    // The access token that just 401'd is already unusable, so there's no
    // authenticated call left to make here — just drop the session
    // locally, same as performRefresh()'s own failure branch does.
    storeTokens(null);
    setTokens(null);
    setUser(null);
    resolve?.(null);
    router.push("/");
  }, [router]);

  useEffect(() => {
    if (!tokens) return;
    authApi
      .fetchMe(tokens.access)
      .then(setUser)
      .catch(() => {
        storeTokens(null);
        setTokens(null);
      })
      .finally(() => setIsLoading(false));
    // Only ever needs to run once, against whatever tokens were in
    // localStorage at mount — applyTokens() is what handles subsequent
    // logins, not a re-run of this effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const applyTokens = useCallback(async (next: StoredTokens) => {
    storeTokens(next);
    setTokens(next);
    const me = await authApi.fetchMe(next.access);
    setUser(me);
    return me;
  }, []);

  const login = useCallback<AuthContextValue["login"]>(
    async (email, password) => {
      const result = await authApi.login(email, password);
      if (isMfaChallenge(result)) {
        return { mfaToken: result.mfa_token };
      }
      const user = await applyTokens(result);
      return { user };
    },
    [applyTokens]
  );

  const completeMfaLogin = useCallback<AuthContextValue["completeMfaLogin"]>(
    async (mfaToken, code) => {
      const result = await authApi.verifyMfaLogin(mfaToken, code);
      return applyTokens(result);
    },
    [applyTokens]
  );

  const register = useCallback<AuthContextValue["register"]>(
    async (email, password) => {
      await authApi.register(email, password);
      const result = await login(email, password);
      if ("mfaToken" in result) {
        // Freshly registered accounts never have MFA enrolled yet, but stay
        // correct if that ever changes rather than silently dropping it.
        throw new Error("Unexpected MFA challenge right after registration.");
      }
    },
    [login]
  );

  const loginWithGoogle = useCallback<AuthContextValue["loginWithGoogle"]>(
    async (idToken) => {
      const result = await authApi.loginWithGoogle(idToken);
      return applyTokens(result);
    },
    [applyTokens]
  );

  const logout = useCallback(async () => {
    if (tokens) {
      await authApi.logout(tokens.access, tokens.refresh).catch(() => {});
    }
    storeTokens(null);
    setTokens(null);
    setUser(null);
    router.push("/");
  }, [tokens, router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken: tokens?.access ?? null,
      isLoading,
      isAuthenticated: user !== null,
      login,
      completeMfaLogin,
      register,
      loginWithGoogle,
      logout,
      setUser,
    }),
    [user, tokens, isLoading, login, completeMfaLogin, register, loginWithGoogle, logout]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
      <SessionExpiredModal
        open={sessionExpired}
        busy={continuing}
        onContinue={handleContinue}
        onCancel={handleCancel}
      />
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
