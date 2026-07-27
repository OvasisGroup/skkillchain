# Security Documentation, Test Plan, and QA Checklist

## 1. Security Architecture Controls
- JWT access token TTL: 15 minutes; refresh token TTL: 30 days with rotation.
- Refresh token invalidation on reuse detection.
- Optional MFA (TOTP/WebAuthn) with policy-based enforcement.
- CSRF protection for cookie-bound endpoints.
- XSS mitigation through strict output encoding and CSP.
- SQL injection prevention through ORM and parameterized queries.
- Rate limiting with Redis bucket strategy by IP/user/device.
- File upload hardening: MIME/type checks, antivirus scan, signed storage keys.
- Video protection: signed playback tokens, watermarking, domain restrictions.
- Live session protection: join URLs gated to registered/enrolled users within the join window only; webhook signature verification for Zoom (`X-Zm-Signature` HMAC) and validation of Google Calendar push-notification channel tokens; instructor conferencing OAuth tokens encrypted at rest and revocable on disconnect.
- Encryption:
  - At rest via KMS-managed keys.
  - In transit via TLS 1.2+.
- Audit logs for all privileged and financial operations.

## 2. OWASP and Compliance
- OWASP ASVS checklist integrated in SDLC.
- Secret scanning and dependency CVE remediation policy.
- PCI-conscious architecture (tokenized card handling by gateways).
- Privacy controls for data subject access and deletion workflows.

## 3. Test Plan

### Unit Tests
- Domain services, serializers, permission guards, adapters.

### Integration Tests
- DB integration for enrollments/payments/progress.
- RabbitMQ/Celery job orchestration and retry behavior.

### API Tests
- Contract tests generated from OpenAPI.
- Negative scenarios for authz/authn/rate limits.

### E2E Tests
- Web and mobile critical paths: signup, purchase, playback, certificate.

### Load Testing
- Baseline: 5K RPS search peak, 1K checkout/minute burst.
- Soak tests on queue-heavy workloads.

### Security Testing
- DAST + auth abuse scenarios.
- Penetration tests before major releases.

## 4. QA Checklist
- Functional:
  - Role-based access validation for each user type.
  - Payment provider fallbacks and webhook correctness.
  - Progress resume and certificate issuance correctness.
- Non-functional:
  - Performance SLO compliance.
  - Accessibility checks (keyboard, screen reader, contrast).
  - Localization/date-currency formatting.
- Operational:
  - Observability dashboards updated.
  - Alert runbooks and on-call readiness.
  - Backup restore drill completed.

## 5. Security Incident Response Summary
- Severity classification (SEV1-SEV4).
- 24/7 on-call and escalation matrix.
- Forensic logging retention.
- Post-incident RCA within 5 business days.
