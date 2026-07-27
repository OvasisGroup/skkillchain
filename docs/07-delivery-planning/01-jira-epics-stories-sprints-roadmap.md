# Jira Epics, User Stories, Sprint Plan, and Development Roadmap

## 1. Jira Epics
- EPIC-01 Identity and Access Management
- EPIC-02 Course Catalog and Search
- EPIC-03 Instructor Authoring and Publishing
- EPIC-04 Learning Experience and Progress
- EPIC-05 Assessments and Certificates
- EPIC-06 Checkout, Payments, Billing, and Refunds
- EPIC-07 Messaging, Notifications, and Community
- EPIC-08 Admin Governance and Moderation
- EPIC-09 Organization and Enterprise Features
- EPIC-10 Analytics and Reporting
- EPIC-11 AI Learning Features
- EPIC-12 Platform Reliability, Security, and DevOps
- EPIC-13 Live Sessions (Zoom / Google Meet Integration)

## 2. User Stories by Epic

### EPIC-01 Identity and Access Management
- US-001: As a guest, I want to register with email/password or Google/Apple/Facebook so I can start learning quickly.
- US-002: As a user, I want to enroll in MFA (TOTP or WebAuthn) so my account is protected against takeover.
- US-003: As a user, I want my refresh token invalidated if reuse is detected so a stolen token can't be replayed.
- US-004: As an admin, I want to assign roles and permissions per context (platform/organization) so access stays least-privilege.

### EPIC-02 Course Catalog and Search
- US-005: As a student, I want to filter courses by price, duration, language, and rating so I can find the right fit fast.
- US-006: As a guest, I want to preview a course's free lessons before purchasing so I can evaluate quality.
- US-007: As a student, I want natural-language search to understand intent, not just keywords, so vague queries still surface relevant courses.

### EPIC-03 Instructor Authoring and Publishing
- US-008: As an instructor, I want to build a course from sections and lessons with drag-to-reorder so authoring is fast.
- US-009: As an instructor, I want to upload a video and get transcoding status so I know when a lesson is ready to publish.
- US-010: As an instructor, I want to submit a course for review so it can be published.
- US-011: As a content reviewer, I want a review checklist and the ability to leave inline feedback so approvals are consistent.

### EPIC-04 Learning Experience and Progress
- US-012: As a student, I want to resume a lesson from my last timestamp so I can continue seamlessly across devices.
- US-013: As a student, I want to take timestamped notes and bookmarks so I can revisit key moments.
- US-014: As a student, I want a continue-learning feed so I always know what to watch next.

### EPIC-05 Assessments and Certificates
- US-015: As a student, I want to attempt a quiz with a limited number of tries so assessment stays fair.
- US-016: As a student, I want to submit code to a judged coding exercise and see pass/fail per test case.
- US-017: As a student, I want a certificate issued automatically when I meet completion rules, verifiable by QR code.
- US-018: As an instructor, I want to grade assignment submissions manually or via AI-assisted suggestions.

### EPIC-06 Checkout, Payments, Billing, and Refunds
- US-019: As a student, I want to pay with a local provider (M-Pesa, Flutterwave, Paystack) as well as cards so checkout works in my region.
- US-020: As a student, I want to apply a coupon or gift card at checkout and see the total update.
- US-021: As a finance officer, I want to reconcile provider payouts and refunds against the ledger.
- US-022: As a student, I want to request a refund within policy and see its status.

### EPIC-07 Messaging, Notifications, and Community
- US-023: As a student, I want to message an instructor about a course and get real-time delivery.
- US-024: As a user, I want in-app, email, SMS, and push notifications so I don't miss important events.
- US-025: As a student, I want to leave a review and rating only after a verified purchase so reviews stay trustworthy.

### EPIC-08 Admin Governance and Moderation
- US-026: As an admin, I want to approve or reject submitted courses with reasons so instructors get actionable feedback.
- US-027: As a super admin, I want immutable audit trails of all privileged and financial operations.
- US-028: As a support agent, I want to manage support tickets with SLA status and assignment.
- US-029: As an admin, I want to manage email and notification templates without a code deploy.

### EPIC-09 Organization and Enterprise Features
- US-030: As an organization admin, I want to assign learning paths and course bundles to employees.
- US-031: As an organization admin, I want cohort-level completion and engagement reporting.

### EPIC-10 Analytics and Reporting
- US-032: As an instructor, I want a revenue and engagement dashboard so I can see what's working.
- US-033: As an admin, I want drop-off analysis per lesson so we can identify weak content.

### EPIC-11 AI Learning Features
- US-034: As a student, I want AI-generated summaries and flashcards for long lessons so I can review efficiently.
- US-035: As a student, I want an AI tutor chat scoped to the current course so answers stay relevant and safe.
- US-036: As an instructor, I want AI-drafted quiz questions from my lesson content that I can edit before publishing.

### EPIC-12 Platform Reliability, Security, and DevOps
- US-037: As a platform engineer, I want blue/green deployments with automatic rollback on SLO burn so releases are safe.
- US-038: As a security engineer, I want rate limiting and bot/fraud detection on checkout so abuse is contained.

### EPIC-13 Live Sessions (Zoom / Google Meet Integration)
- US-039: As an instructor, I want to connect my Zoom or Google account so live sessions are hosted under my own identity.
- US-040: As an instructor, I want to schedule a live session for my course with a time, timezone, and optional capacity, and have the meeting created automatically.
- US-041: As a student, I want to register for a live session and receive reminders before it starts.
- US-042: As a student, I want the join link only when the session is about to start, so links can't be shared or reused after the fact.
- US-043: As a student, I want to watch the recording afterward if I couldn't attend live.
- US-044: As an instructor, I want to see who registered and attended so I can gauge engagement.

## 3. Sprint Plan (Initial 8 Sprints, 2 Weeks Each)
- Sprint 1: Foundations (auth core, repo, CI/CD baseline, environments).
- Sprint 2: Catalog and course detail pages + search indexing skeleton.
- Sprint 3: Instructor authoring (course/section/lesson/resource).
- Sprint 4: Checkout + payment provider adapters + webhooks.
- Sprint 5: Enrollment, progress tracking, player session telemetry.
- Sprint 6: Assessments, certificates, notifications, live session scheduling (Zoom/Google Meet adapters, registration, join gating).
- Sprint 7: Admin moderation, reports, audit logs, support module.
- Sprint 8: Hardening (performance, security tests, DR drills, launch readiness).

## 4. Release Roadmap
- Quarter 1:
  - MVP marketplace and student/instructor core.
- Quarter 2:
  - Enterprise org controls, advanced analytics, affiliate maturity.
- Quarter 3:
  - AI tutor, adaptive recommendations, deeper localization.
- Quarter 4:
  - Multi-region optimization and ecosystem integrations.

## 5. Delivery Governance
- Definition of Ready:
  - User story has acceptance criteria, dependencies, and test approach.
- Definition of Done:
  - Code merged, tests green, security checks pass, observability added, docs updated.
- Risk Review:
  - Weekly architecture and security review board.
