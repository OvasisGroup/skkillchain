# Platform Folder Structure and App Boundaries

## 1. Monorepo Layout
```text
skillchain/
  backend/
    manage.py
    pyproject.toml
    config/
      settings/
        base.py
        dev.py
        stage.py
        prod.py
      urls.py
      asgi.py
      wsgi.py
    apps/
      identity/
      authorization/
      organizations/
      catalog/
      content/
      learning/
      live_sessions/
      assessments/
      commerce/
      billing/
      payouts/
      affiliates/
      messaging/
      notifications/
      certificates/
      analytics/
      search/
      recommendations/
      ai/
      cms/
      support/
      moderation/
      audit/
      platform_settings/
    shared/
      db/
      events/
      security/
      storage/
      observability/
      utils/
    tests/
      unit/
      integration/
      api/
      e2e/
  web/
    nextjs-app/
  mobile/
    flutter-app/
  infra/
    docker/
    kubernetes/
    terraform/
    github-actions/
  docs/
```

## 2. Django App Responsibilities
- identity: registration/login/social auth/JWT/MFA/session security.
- authorization: roles, permissions, policy checks.
- catalog: courses, categories, tags, discovery views.
- content: sections, lessons, video/resource metadata.
- learning: enrollment/progress/continue-learning/bookmarks/notes.
- live_sessions: conferencing account connections, session scheduling, registration, join gating, recording ingestion (Zoom/Google Meet adapters).
- assessments: quizzes, questions, attempts, assignments, coding exercises.
- commerce: cart/order/checkout/coupon/gift card.
- billing: payments, invoices, taxes, refunds, subscriptions.
- payouts: instructor revenue and payout requests.
- affiliates: referrals and commission lifecycle.
- messaging: direct/group threads and real-time chat.
- notifications: email/sms/push/in-app event fan-out.
- certificates: issue/verify/download certificates.
- analytics: event ingestion and report endpoints.
- search: Elasticsearch indexing and query services.
- recommendations: ranking/recommendation orchestration.
- ai: tutor, summarization, quiz generation workflows.
- cms: blog, static pages, seo metadata.
- support/moderation/audit: operational governance.

## 3. Next.js Structure
```text
web/nextjs-app/
  src/
    app/
      (public)/
      (student)/
      (instructor)/
      (organization)/
      (admin)/
      api/
    features/
      auth/
      catalog/
      course-player/
      live-sessions/
      checkout/
      dashboard-student/
      dashboard-instructor/
      admin/
      messaging/
      notifications/
    components/
      ui/
      forms/
      charts/
      player/
    lib/
      api-client/
      auth/
      analytics/
    styles/
```

## 4. Flutter Structure
```text
mobile/flutter-app/
  lib/
    core/
      networking/
      auth/
      storage/
      theme/
    features/
      auth/
      catalog/
      player/
      learning/
      live_sessions/
      checkout/
      profile/
      notifications/
      messaging/
    shared/
      widgets/
      models/
      utils/
  test/
```

## 5. Design Rules
- Shared contracts generated from OpenAPI.
- Domain services isolate external providers (payments/video/conferencing/ai).
- No cross-app data access without explicit service interface.
- Event schema versioning required for async consumers.
