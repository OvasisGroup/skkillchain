"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { ApiError } from "@/lib/api/client";
import { listTicketMessages, postTicketMessage } from "@/lib/api/support";
import type { SupportTicketMessage } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

export default function SupportTicketDetailPage() {
  const params = useParams<{ ticketId: string }>();
  const { accessToken, user } = useAuth();
  const [messages, setMessages] = useState<SupportTicketMessage[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listTicketMessages(params.ticketId, accessToken)
      .then((page) => {
        if (!cancelled) setMessages(page.results);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 403) {
          setError(
            "You're not a party to this ticket yet — assign it to yourself from the ticket list to view and reply to messages."
          );
        } else {
          setError(err instanceof ApiError ? err.message_ : "Couldn't load this ticket's messages.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, params.ticketId]);

  async function handleSend() {
    if (!accessToken || !reply.trim()) return;
    setSending(true);
    try {
      const message = await postTicketMessage(params.ticketId, reply, accessToken);
      setMessages((prev) => [...(prev ?? []), message]);
      setReply("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't send this reply.");
    } finally {
      setSending(false);
    }
  }

  if (error) return <ErrorState message={error} />;
  if (!messages) return <LoadingState label="Loading ticket messages…" />;

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/dashboard/support"
          className="flex items-center gap-1.5 text-sm text-foreground/50 hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to tickets
        </Link>
      </div>
      <PageHeader eyebrow="Ticket" title="Conversation" />

      <div className="rounded-2xl border border-border bg-surface p-5 sm:p-6">
        <div className="space-y-3">
          {messages.length === 0 ? (
            <p className="text-sm text-foreground/50">No messages yet.</p>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`max-w-xl rounded-xl border border-border p-3 text-sm ${
                  message.sender === user?.id ? "ml-auto bg-teal-400/10" : "bg-background/40"
                }`}
              >
                <p className="text-foreground">{message.body}</p>
                <p className="mt-1 text-xs text-foreground/40">
                  {new Date(message.created_at).toLocaleString()}
                </p>
              </div>
            ))
          )}
        </div>

        <div className="mt-4 flex gap-2">
          <input
            type="text"
            value={reply}
            onChange={(e) => setReply(e.target.value)}
            placeholder="Write a reply…"
            className="flex-1 rounded-lg border border-border-strong bg-surface px-3 py-2 text-sm text-foreground focus:border-teal-400 focus:outline-none"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={sending || !reply.trim()}
            className="rounded-lg bg-teal-400 px-4 py-2 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {sending ? "Sending…" : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}
