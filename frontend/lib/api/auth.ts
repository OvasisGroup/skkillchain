import { apiFetch } from "./client";
import type { LoginResult, Me, Profile, TokenPair } from "./types";

export function register(email: string, password: string): Promise<Me> {
  return apiFetch<Me>("/auth/register/", { method: "POST", body: { email, password } });
}

export function login(email: string, password: string): Promise<LoginResult> {
  return apiFetch<LoginResult>("/auth/login/", { method: "POST", body: { email, password } });
}

export function verifyMfaLogin(mfaToken: string, code: string): Promise<TokenPair> {
  return apiFetch<TokenPair>("/auth/mfa/login-verify/", {
    method: "POST",
    body: { mfa_token: mfaToken, code },
  });
}

// Same endpoint handles both login and signup — the backend creates the
// account on first sign-in if no matching user/identity exists yet, so
// there's no separate "register with Google" call.
export function loginWithGoogle(idToken: string): Promise<TokenPair> {
  return apiFetch<TokenPair>("/auth/oauth/google/token/", {
    method: "POST",
    body: { token: idToken },
  });
}

export function fetchMe(accessToken: string): Promise<Me> {
  return apiFetch<Me>("/auth/me/", { token: accessToken });
}

export function updateMe(
  input: { email?: string; profile?: Partial<Omit<Profile, "avatar">> },
  accessToken: string
): Promise<Me> {
  return apiFetch<Me>("/auth/me/", { method: "PATCH", token: accessToken, body: input });
}

// Separate from updateMe() — the avatar is a file, so it needs its own
// multipart request against POST /auth/me/avatar/.
export function uploadAvatar(file: File, accessToken: string): Promise<Me> {
  const form = new FormData();
  form.set("avatar", file);
  return apiFetch<Me>("/auth/me/avatar/", { method: "POST", token: accessToken, body: form });
}

export function enrollMfa(accessToken: string): Promise<{ provisioning_uri: string; secret: string }> {
  return apiFetch("/auth/mfa/enroll/", { method: "POST", token: accessToken });
}

export function verifyMfa(code: string, accessToken: string): Promise<{ status: string }> {
  return apiFetch("/auth/mfa/verify/", { method: "POST", token: accessToken, body: { code } });
}

export function logout(accessToken: string, refreshToken: string): Promise<void> {
  return apiFetch<void>("/auth/logout/", {
    method: "POST",
    token: accessToken,
    body: { refresh: refreshToken },
  });
}
