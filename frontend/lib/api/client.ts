import type { ProblemDetail } from "./types";

// `||`, not `??` — a Docker build-arg that's declared but not passed a
// value surfaces here as an empty string, not undefined, and `??` only
// falls back on null/undefined. An empty string here means every request
// silently goes to a relative path instead of the real API host.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

// DRF's error shapes aren't as uniform as ProblemDetail's type claims — a
// manually raised `ValidationError({"field": "some message"})` (as opposed
// to the usual `{"field": ["some message"]}`) serializes a bare string, and
// nested serializers produce nested objects. Recursing here means a field's
// value can be any of those without message_ throwing while trying to
// report an error to the user.
function stringifyErrorValue(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(stringifyErrorValue).join(" ");
  if (value && typeof value === "object") {
    return Object.entries(value)
      .map(([field, nested]) => `${field}: ${stringifyErrorValue(nested)}`)
      .join(" ");
  }
  return String(value);
}

export class ApiError extends Error {
  status: number;
  problem: ProblemDetail;

  constructor(problem: ProblemDetail) {
    super(problem.detail ?? problem.title ?? "Request failed");
    this.status = problem.status;
    this.problem = problem;
  }

  /** Flattens field-level validation errors into one readable string. */
  get message_(): string {
    const { errors } = this.problem;
    if (typeof errors === "string") return errors;
    // DRF wraps a plain-string ValidationError(...) as a bare one-element
    // list, not a {field: [...]} dict — so this has to be checked before
    // the object branch below (arrays are typeof "object" in JS too).
    if (Array.isArray(errors)) return errors.map(stringifyErrorValue).join(" ");
    if (errors && typeof errors === "object") {
      return Object.entries(errors)
        .map(([field, messages]) => `${field}: ${stringifyErrorValue(messages)}`)
        .join(" ");
    }
    return this.problem.detail ?? this.message;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  token?: string;
}

// Set by AuthContext once a session exists. Resolves to a fresh access token
// after refreshing (and persisting the rotated refresh token), or null if
// the refresh token itself is no longer valid — 15-minute access tokens mean
// this fires routinely, not just after long idle periods.
type RefreshHandler = () => Promise<string | null>;
let refreshHandler: RefreshHandler | null = null;
// Concurrent 401s during the same tick must share one refresh call — the
// backend blacklists the old refresh token on rotation, so a second call
// made before the first resolves would invalidate the session.
let refreshPromise: Promise<string | null> | null = null;

export function setRefreshHandler(handler: RefreshHandler | null): void {
  refreshHandler = handler;
}

function requestRefresh(): Promise<string | null> {
  if (!refreshHandler) return Promise.resolve(null);
  if (!refreshPromise) {
    refreshPromise = refreshHandler().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function rawFetch(
  path: string,
  { body, headers, ...rest }: Omit<RequestOptions, "token">,
  token: string | undefined
): Promise<Response> {
  const isFormData = body instanceof FormData;
  return fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      // FormData bodies must NOT set Content-Type manually — fetch sets it
      // itself (including the multipart boundary) only when left unset.
      ...(body !== undefined && !isFormData ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: isFormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
  });
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const isJson = response.headers.get("content-type")?.includes("json");
  const data = isJson ? await response.json() : undefined;

  if (!response.ok) {
    const problem: ProblemDetail =
      data ?? { type: "about:blank", title: response.statusText, status: response.status };
    throw new ApiError(problem);
  }

  return data as T;
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, ...rest } = options;
  const response = await rawFetch(path, rest, token);

  // Only authenticated requests are eligible for retry — an unauthenticated
  // 401 (e.g. bad login credentials) has no token to refresh.
  if (response.status === 401 && token) {
    const newToken = await requestRefresh();
    if (newToken) {
      return parseResponse<T>(await rawFetch(path, rest, newToken));
    }
  }

  return parseResponse<T>(response);
}
