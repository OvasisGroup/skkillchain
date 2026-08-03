import { apiFetch } from "./client";
import type { Setting } from "./types";

export function listSettings(token: string): Promise<Setting[]> {
  return apiFetch<Setting[]>("/admin/settings/", { token, cache: "no-store" });
}

export function upsertSetting(
  key: string,
  valueJson: unknown,
  token: string
): Promise<Setting> {
  return apiFetch<Setting>("/admin/settings/", {
    method: "PATCH",
    token,
    body: { key, value_json: valueJson },
  });
}
