"use client";

import { FileCheck, Mail } from "lucide-react";
import { useEffect, useState } from "react";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { EmailTemplateRow } from "@/components/dashboard/EmailTemplateRow";
import { NotificationTemplateRow } from "@/components/dashboard/NotificationTemplateRow";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { Panel } from "@/components/dashboard/Panel";
import { RejectCourseButton } from "@/components/dashboard/RejectCourseButton";
import { StatCard } from "@/components/dashboard/StatCard";
import { approveCourse, listPendingCourses, rejectCourse } from "@/lib/api/catalogAdmin";
import { ApiError } from "@/lib/api/client";
import { listEmailTemplates, listNotificationTemplates } from "@/lib/api/templates";
import type { Course, EmailTemplate, NotificationTemplate } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";
import { Reveal } from "@/components/animation/Reveal";

export default function ContentReviewerDashboardPage() {
  const { accessToken } = useAuth();
  const [pendingCourses, setPendingCourses] = useState<Course[] | null>(null);
  const [notificationTemplates, setNotificationTemplates] = useState<NotificationTemplate[]>([]);
  const [emailTemplates, setEmailTemplates] = useState<EmailTemplate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyCourseId, setBusyCourseId] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    Promise.all([
      listPendingCourses(accessToken),
      listNotificationTemplates(accessToken),
      listEmailTemplates(accessToken),
    ])
      .then(([coursesPage, notifications, emails]) => {
        if (cancelled) return;
        setPendingCourses(coursesPage.results);
        setNotificationTemplates(notifications);
        setEmailTemplates(emails);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message_ : "Couldn't load the review queue.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function handleApprove(courseId: string) {
    if (!accessToken) return;
    setBusyCourseId(courseId);
    try {
      await approveCourse(courseId, accessToken);
      setPendingCourses((prev) => prev?.filter((c) => c.id !== courseId) ?? prev);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't approve this course.");
    } finally {
      setBusyCourseId(null);
    }
  }

  async function handleReject(courseId: string, reason: string) {
    if (!accessToken) return;
    setBusyCourseId(courseId);
    try {
      await rejectCourse(courseId, reason, accessToken);
      setPendingCourses((prev) => prev?.filter((c) => c.id !== courseId) ?? prev);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't reject this course.");
    } finally {
      setBusyCourseId(null);
    }
  }

  if (error) return <ErrorState message={error} />;
  if (!pendingCourses) return <LoadingState label="Loading the review queue…" />;

  return (
    <div className="space-y-8">
      <PageHeader title="Content Reviewer" />

      <Reveal className="grid grid-cols-2 gap-4 sm:grid-cols-4" stagger={0.08}>
        <StatCard label="Pending courses" value={String(pendingCourses.length)} icon={FileCheck} />
        <StatCard label="Templates" value={String(notificationTemplates.length + emailTemplates.length)} icon={Mail} />
      </Reveal>

      <Panel title="Course approval queue">
        <DataTable
          rows={pendingCourses}
          getRowKey={(c) => c.id}
          emptyMessage="No courses are waiting for review."
          columns={[
            { header: "Title", cell: (c) => c.title },
            { header: "Instructor", cell: (c) => c.instructor.email },
            { header: "Price", cell: (c) => `${c.currency} ${c.price_amount}` },
            {
              header: "",
              cell: (c) => (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleApprove(c.id)}
                    disabled={busyCourseId === c.id}
                    className="rounded-full bg-teal-400 px-3 py-1 text-xs font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:opacity-50"
                  >
                    Approve
                  </button>
                  <RejectCourseButton
                    busy={busyCourseId === c.id}
                    onReject={(reason) => handleReject(c.id, reason)}
                  />
                </div>
              ),
            },
          ]}
        />
      </Panel>

      <Panel title="Notification templates">
        <div className="space-y-3">
          {notificationTemplates.length === 0 ? (
            <p className="text-sm text-foreground/50">No notification templates found.</p>
          ) : (
            notificationTemplates.map((template) => (
              <NotificationTemplateRow
                key={`${template.code}-${template.locale}`}
                template={template}
                onUpdated={(updated) =>
                  setNotificationTemplates((prev) =>
                    prev.map((t) => (t.code === updated.code && t.locale === updated.locale ? updated : t))
                  )
                }
              />
            ))
          )}
        </div>
      </Panel>

      <Panel title="Email templates">
        <div className="space-y-3">
          {emailTemplates.length === 0 ? (
            <p className="text-sm text-foreground/50">No email templates found.</p>
          ) : (
            emailTemplates.map((template) => (
              <EmailTemplateRow
                key={`${template.code}-${template.locale}`}
                template={template}
                onUpdated={(updated) =>
                  setEmailTemplates((prev) =>
                    prev.map((t) => (t.code === updated.code && t.locale === updated.locale ? updated : t))
                  )
                }
              />
            ))
          )}
        </div>
      </Panel>
    </div>
  );
}
