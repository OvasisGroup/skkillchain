"use client";

import { FileText, Settings as SettingsIcon, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { Panel } from "@/components/dashboard/Panel";
import { StatCard } from "@/components/dashboard/StatCard";
import { listUsers, updateUserStatus } from "@/lib/api/admin";
import { listAuditLogs } from "@/lib/api/audit";
import { ApiError } from "@/lib/api/client";
import { listSettings, upsertSetting } from "@/lib/api/settings";
import type { AdminUser, AuditLog, Setting } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

function SettingUpsertForm({ onSaved }: { onSaved: (setting: Setting) => void }) {
  const { accessToken } = useAuth();
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken || !key) return;
    setSaving(true);
    setError(null);
    try {
      let parsedValue: unknown = value;
      try {
        parsedValue = JSON.parse(value);
      } catch {
        // Plain strings are valid JSON values too — fall back to the raw string.
      }
      const setting = await upsertSetting(key, parsedValue, accessToken);
      onSaved(setting);
      setKey("");
      setValue("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't save this setting.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2 rounded-xl border border-border bg-surface p-4">
      <div>
        <label className="block text-xs font-medium text-foreground/60">Key</label>
        <input
          type="text"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          className="mt-1 w-48 rounded-lg border border-border-strong bg-surface px-2 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-foreground/60">Value (JSON or text)</label>
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="mt-1 w-64 rounded-lg border border-border-strong bg-surface px-2 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
        />
      </div>
      <button
        type="submit"
        disabled={saving || !key}
        className="rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {saving ? "Saving…" : "Save setting"}
      </button>
      {error && <p className="w-full text-xs text-rose-400">{error}</p>}
    </form>
  );
}

export default function AdminDashboardPage() {
  const { accessToken } = useAuth();
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [emailSearch, setEmailSearch] = useState("");
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [settings, setSettings] = useState<Setting[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyUserId, setBusyUserId] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    Promise.all([listUsers(accessToken), listAuditLogs(accessToken), listSettings(accessToken)])
      .then(([usersPage, auditPage, settingsData]) => {
        if (cancelled) return;
        setUsers(usersPage.results);
        setAuditLogs(auditPage.results);
        setSettings(settingsData);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message_ : "Couldn't load admin data.");
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken) return;
    try {
      const page = await listUsers(accessToken, emailSearch || undefined);
      setUsers(page.results);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't search users.");
    }
  }

  async function handleToggleStatus(user: AdminUser) {
    if (!accessToken) return;
    setBusyUserId(user.id);
    try {
      const updated = await updateUserStatus(user.id, !user.is_active, accessToken);
      setUsers((prev) => prev?.map((u) => (u.id === user.id ? updated : u)) ?? prev);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't update this user.");
    } finally {
      setBusyUserId(null);
    }
  }

  if (error) return <ErrorState message={error} />;
  if (!users) return <LoadingState label="Loading admin dashboard…" />;

  const activeCount = users.filter((u) => u.is_active).length;

  return (
    <div className="space-y-8">
      <PageHeader title="Administrator" />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Users" value={String(users.length)} icon={Users} />
        <StatCard label="Active" value={String(activeCount)} icon={Users} />
        <StatCard label="Audit events" value={String(auditLogs.length)} icon={FileText} />
        <StatCard label="Settings" value={String(settings.length)} icon={SettingsIcon} />
      </div>

      <Panel title="Users">
        <form onSubmit={handleSearch} className="mb-3 flex gap-2">
          <input
            type="text"
            value={emailSearch}
            onChange={(e) => setEmailSearch(e.target.value)}
            placeholder="Search by email…"
            className="w-64 rounded-lg border border-border-strong bg-surface px-3 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
          />
          <button
            type="submit"
            className="rounded-full border border-border-strong px-4 py-1.5 text-sm font-semibold text-foreground/80 hover:bg-surface-hover"
          >
            Search
          </button>
        </form>
        <DataTable
          rows={users}
          getRowKey={(u) => u.id}
          emptyMessage="No users found."
          columns={[
            { header: "Email", cell: (u) => u.email },
            {
              header: "Status",
              cell: (u) => (
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    u.is_active ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
                  }`}
                >
                  {u.is_active ? "Active" : "Suspended"}
                </span>
              ),
            },
            { header: "Joined", cell: (u) => new Date(u.created_at).toLocaleDateString() },
            {
              header: "",
              cell: (u) => (
                <button
                  type="button"
                  onClick={() => handleToggleStatus(u)}
                  disabled={busyUserId === u.id}
                  className="rounded-full border border-border-strong px-3 py-1 text-xs font-semibold text-foreground/80 hover:bg-surface-hover disabled:opacity-50"
                >
                  {u.is_active ? "Suspend" : "Reinstate"}
                </button>
              ),
            },
          ]}
        />
      </Panel>

      <Panel title="Audit log">
        <DataTable
          rows={auditLogs}
          getRowKey={(a) => a.id}
          emptyMessage="No audit events recorded yet."
          columns={[
            { header: "Actor", cell: (a) => a.actor_email || "—" },
            { header: "Action", cell: (a) => a.action },
            { header: "Entity", cell: (a) => a.entity_type },
            { header: "When", cell: (a) => new Date(a.created_at).toLocaleString() },
          ]}
        />
      </Panel>

      <Panel title="Platform settings">
        <div className="space-y-3">
          <SettingUpsertForm
            onSaved={(setting) =>
              setSettings((prev) => {
                const exists = prev.some((s) => s.key === setting.key);
                return exists ? prev.map((s) => (s.key === setting.key ? setting : s)) : [setting, ...prev];
              })
            }
          />
          <DataTable
            rows={settings}
            getRowKey={(s) => s.id}
            emptyMessage="No platform settings configured yet."
            columns={[
              { header: "Key", cell: (s) => s.key },
              { header: "Value", cell: (s) => JSON.stringify(s.value_json) },
              { header: "Updated", cell: (s) => new Date(s.updated_at).toLocaleString() },
            ]}
          />
        </div>
      </Panel>
    </div>
  );
}
