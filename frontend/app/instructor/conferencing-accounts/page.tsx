import { redirect } from "next/navigation";

// The OAuth callback (backend apps/live_sessions/views.py
// ConferencingAccountCallbackView) redirects the browser to this exact
// path via settings.PUBLIC_APP_URL — it's hardcoded server-side, so this
// route has to exist even though the real page lives under /dashboard.
// This just forwards the connected/error query params along.
export default async function ConferencingAccountsRedirect({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (typeof value === "string") query.set(key, value);
  }
  const qs = query.toString();
  redirect(`/dashboard/instructor/conferencing-accounts${qs ? `?${qs}` : ""}`);
}
