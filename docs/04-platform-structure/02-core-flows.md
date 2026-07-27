# Authentication and Core Business Flows

## 1. Authentication Flow
```mermaid
sequenceDiagram
  participant U as User
  participant C as Client
  participant A as Auth API
  participant O as OAuth Provider
  participant R as Redis
  U->>C: Login request
  C->>A: Credentials/OAuth token
  alt OAuth
    A->>O: Verify provider token
    O-->>A: User identity
  end
  A->>A: Validate + risk checks + MFA challenge if required
  A->>R: Store refresh token jti/session
  A-->>C: Access JWT + Refresh token
```

## 2. Course Creation and Approval Flow
```mermaid
sequenceDiagram
  participant I as Instructor
  participant API as Course API
  participant VID as Video Provider
  participant REV as Content Reviewer
  participant ADM as Admin
  I->>API: Create course draft
  I->>API: Upload lessons/resources
  API->>VID: Create protected playback assets
  I->>API: Submit for review
  REV->>API: Review checklist and feedback
  alt Approved
    ADM->>API: Approve and publish
  else Rejected
    REV->>API: Reject with reasons
  end
```

## 3. Enrollment Flow
```mermaid
sequenceDiagram
  participant S as Student
  participant API as Commerce API
  participant PAY as Payment Gateway
  participant LRN as Learning API
  S->>API: Create order for course/subscription
  API->>PAY: Initiate payment
  PAY-->>API: Payment success webhook
  API->>LRN: Create enrollment
  LRN-->>S: Access granted to course
```

## 4. Payment and Refund Flow
- Order creation with tax/coupon validation.
- Payment intent/authorization at provider.
- Webhook reconciliation and idempotent settlement update.
- Invoice generation and notification dispatch.
- Refund request -> eligibility policy -> provider refund -> ledger update.

## 5. Certificate Generation Flow
- Completion rule evaluator confirms all mandatory units passed.
- Certificate service generates unique ID + QR payload.
- PDF renderer creates signed certificate artifact in S3.
- Verification endpoint validates ID and checksum.

## 6. Instructor Approval Flow
- Instructor application with KYC/tax profile.
- Compliance checks by moderation/finance.
- Approval sets role + payout account eligibility.

## 7. Admin Workflow
- Intake queues: pending courses, flagged reviews, support tickets, fraud alerts.
- Decision actions create immutable audit log records.
- Operational reports for finance, support, and trust & safety.

## 8. OAuth Social Login Flow

```mermaid
sequenceDiagram
  participant U as User
  participant C as Client (Web/Mobile)
  participant P as Provider (Google/Apple/Facebook)
  participant API as Auth API

  C->>P: Provider's own OAuth SDK flow
  P-->>C: ID token (Google/Apple) or access token (Facebook)
  C->>API: POST /auth/oauth/{provider}/token { token }
  API->>P: Verify token (JWKS signature check, or Graph API call)
  P-->>API: Verified claims: provider_user_id, email, email_verified
  alt Existing OAuthIdentity
    API->>API: Look up linked user
  else No identity yet, email matches an existing account
    alt Provider verified the email
      API->>API: Link new OAuthIdentity to existing user
    else Email not verified by provider
      API-->>C: 401 — log in with password instead
    end
  else No identity, no matching account
    API->>API: Create new user (unusable password) + OAuthIdentity
  end
  API-->>C: Access + refresh JWT (same shape as password login)
```

The client drives the OAuth exchange with the provider's own SDK (Google Sign-In, Sign in with Apple, Facebook Login) rather than the backend running a server-side redirect flow — this platform serves both a Next.js web client and a native Flutter client, and token verification is the one pattern that's uniform across both instead of needing a redirect flow for web and a native-SDK flow for mobile.

- An unverified email is never used to silently link to an existing account — that would let an attacker who controls a weaker provider hijack a real user's account by claiming their email address.
- Apple only returns an email on the user's *first* authorization for a given app; a returning user is recognized by their already-linked `OAuthIdentity`, not by email.

## 9. Live Session Scheduling and Join Flow

### Scheduling
```mermaid
sequenceDiagram
  participant I as Instructor
  participant API as Live Session API
  participant CONF as Conferencing Adapter
  participant PROV as Zoom / Google Meet
  participant N as Notification Service
  I->>API: Connect Zoom or Google account (OAuth)
  API->>PROV: Exchange code for tokens
  PROV-->>API: Access/refresh tokens
  API->>API: Store encrypted tokens in conferencing_accounts
  I->>API: Schedule live session for course (time, timezone, capacity)
  API->>CONF: create_meeting(session)
  CONF->>PROV: Create meeting via provider API
  PROV-->>CONF: join_url, host_join_url, external_meeting_id
  CONF-->>API: Meeting created
  API->>N: Notify enrolled students session is available
```

### Registration, Join, and Recording
```mermaid
sequenceDiagram
  participant S as Student
  participant API as Live Session API
  participant N as Notification Service
  participant PROV as Zoom / Google Meet
  S->>API: Register for live session (must be enrolled)
  API-->>S: Registration confirmed
  N->>S: Reminder notification (T-24h, T-15m)
  S->>API: GET join URL at session time
  API->>API: Verify registration + join window
  API-->>S: join_url (redirect to provider)
  Note over PROV: Session runs on provider platform
  PROV-->>API: meeting.ended / recording.completed (Zoom webhook)<br/>or polled via Drive API (Google Meet)
  API->>API: Store live_session_recordings, mark attendance
  API->>N: Notify registrants recording is ready
```

- Join links are never issued outside the join window (default: 15 minutes before start through session end) even to registered students, to prevent link sharing/leakage.
- Zoom recording availability arrives via the `recording.completed` webhook; Google Meet has no equivalent webhook, so a Celery Beat task polls the Google Drive API for the recording file starting at `scheduled_end_at`.
- If a session ends with no recording detected after a timeout window, support is alerted and affected registrants are notified so a manual resolution (reschedule, partial refund) can be issued.

## 10. User Journey Maps (Condensed)

### Student
- Discover course -> evaluate social proof -> checkout -> onboarding -> active learning (incl. registering for and attending live sessions) -> assessment -> certificate -> share/upsell.

### Instructor
- Register -> complete verification -> create content -> submit review -> publish -> engage learners -> receive payout -> iterate course.

### Organization Admin
- Configure org -> invite users -> assign paths -> monitor outcomes -> renew subscription.
