import type { ProblemDetail } from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

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

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, token, headers, ...rest } = options;
  const isFormData = body instanceof FormData;

  const response = await fetch(`${API_BASE_URL}${path}`, {
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
