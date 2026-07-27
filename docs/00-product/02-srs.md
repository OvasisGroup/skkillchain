# Software Requirements Specification (SRS)

## 1. System Overview
A multi-tenant SaaS learning platform exposing REST and WebSocket interfaces for web/mobile clients, integrated with external payment, media, and communication providers.

## 2. Actors and Permissions (Summary)
- Guest: browse/search catalog, preview content.
- Student: enroll, consume, assess, review, message, subscribe.
- Instructor: author/manage courses, coupons, analytics, payouts.
- Org Admin: manage users/paths/reporting/billing.
- Reviewer/Moderator/Support/Finance/Admin/Super Admin: governance and operations.

## 3. Functional Requirements

### 3.1 Identity and Access
- FR-AUTH-001: Support email/password + OAuth social login.
- FR-AUTH-002: Issue JWT access/refresh tokens with rotation.
- FR-AUTH-003: Support MFA enrollment and verification.
- FR-AUTH-004: Enforce RBAC permissions on all APIs.

### 3.2 Course and Content
- FR-CRS-001: Create/edit/publish/archive courses.
- FR-CRS-002: Manage sections, lessons, and assets.
- FR-CRS-003: Provide subtitles, transcripts, and previews.
- FR-CRS-004: Capture learning objectives and prerequisites.

### 3.3 Learning Experience
- FR-LRN-001: Track per-lesson progress and resume playback.
- FR-LRN-002: Support notes/bookmarks and continue-learning feed.
- FR-LRN-003: Generate certificates upon completion rules.
- FR-LRN-004: Support quizzes/assignments/coding exercises.

### 3.3a Live Sessions
- FR-LIVE-001: Instructor connects a Zoom or Google account so sessions are hosted under their own identity.
- FR-LIVE-002: Instructor schedules a live session against a course (or as a standalone cohort event) with title, agenda, start/end time, timezone, and optional capacity.
- FR-LIVE-003: System creates the remote meeting via the provider adapter at schedule time and stores the join URL, host URL, and external meeting ID.
- FR-LIVE-004: Enrolled students register for a live session; the join link is only issued to registered, enrolled students within the join window (default: 15 minutes before start through session end).
- FR-LIVE-005: System sends reminder notifications (email/push/in-app) at configurable offsets before session start.
- FR-LIVE-006: System ingests recording-ready events from the provider (webhook where available, polling fallback for providers without one) and exposes recordings to registrants after the session ends.
- FR-LIVE-007: Instructor can reschedule or cancel a session; cancellation notifies all registrants and triggers refund-eligibility evaluation for paid live add-ons.
- FR-LIVE-008: System records attendance (joined_at/left_at/duration) where the provider API exposes participant data, for engagement analytics.

### 3.4 Commerce
- FR-PAY-001: One-time purchase with tax/coupon support.
- FR-PAY-002: Subscription billing and renewal lifecycle.
- FR-PAY-003: Refund and invoice generation.
- FR-PAY-004: Affiliate commission and instructor revenue split.

### 3.5 Communication
- FR-COM-001: In-app/email/SMS/push notifications.
- FR-COM-002: Real-time messaging and discussions via WebSockets.
- FR-COM-003: Support ticket workflow with role assignment.

### 3.6 Admin and Governance
- FR-ADM-001: User/instructor/course moderation workflows.
- FR-ADM-002: CMS/blog/SEO templates and site settings.
- FR-ADM-003: Fraud and audit management.
- FR-ADM-004: Role/permission management.

### 3.7 AI Capabilities
- FR-AI-001: Recommendation engine with explainable factors.
- FR-AI-002: AI tutor chat with context boundaries.
- FR-AI-003: Quiz/summary/flashcard generation.
- FR-AI-004: Transcript/subtitle generation pipeline.

## 4. Non-Functional Requirements
- NFR-SEC-001: TLS 1.2+, JWT signing key rotation, secrets manager.
- NFR-SEC-002: OWASP controls (CSRF, XSS, SQLi, SSRF mitigations).
- NFR-PERF-001: P95 < 300ms for catalog APIs under target load.
- NFR-PERF-002: P95 websocket notification delivery < 2 seconds.
- NFR-REL-001: Zero data loss for payment and enrollment events.
- NFR-OBS-001: 100% request tracing on critical APIs.

## 5. External Interfaces
- Payment APIs: Stripe/PayPal/Flutterwave/Paystack/MPESA.
- Video APIs: Mux/Bunny/Vimeo.
- Conferencing APIs: Zoom (Meetings API, Server-to-Server or per-instructor OAuth), Google Meet (Google Calendar API `conferenceData`, per-instructor OAuth).
- OAuth APIs: Google/Apple/Facebook.
- Notification providers: SMTP/SMS/Push.

## 6. Data Requirements
- PostgreSQL as system of record.
- Redis for cache, rate limits, token blacklist checks.
- Elasticsearch for full-text and faceted course search.

## 7. Constraints and Assumptions
- Payment card data never stored directly (tokenization only).
- Geo/legal tax rules configured via pluggable engine.
- AI outputs for high-stakes grading require policy checks and human override.

## 8. Acceptance Criteria
- End-to-end flows validated: auth, course publication, enrollment, payment, learning progression, certificate issuance, payout reconciliation.
- Security and performance tests pass defined gates.
