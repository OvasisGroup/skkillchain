# UX, Wireframes, High-Fidelity UI, and Design System

## 1. Experience Principles
- Clarity first for learning outcomes and progress.
- Minimize friction for checkout, enrollment, and playback resume.
- Preserve contextual focus while learning (low cognitive switching).
- Accessible by default (WCAG 2.2 AA).

## 2. User Journey Maps (Detailed)

### Student Journey
- Awareness: SEO landing, recommendations, referrals.
- Consideration: syllabus preview, instructor trust, ratings, duration.
- Conversion: checkout with local payment options and coupons.
- Activation: onboarding checklist + learning goal capture.
- Engagement: continue-learning rail, reminders, streaks, AI summaries.
- Outcome: certificate issuance and social share.

### Instructor Journey
- Acquisition: instructor signup, profile, compliance/KYC.
- Authoring: course blueprint, video upload, quiz creation.
- Governance: review feedback loop and moderation.
- Growth: coupons, affiliate setup, announcements.
- Retention: earnings analytics, engagement and churn insights.

### Org Admin Journey
- Setup: tenant branding, SSO (future), invites.
- Allocation: assign bundles/learning paths.
- Tracking: cohort performance and compliance reporting.

## 3. Low-Fidelity Wireframes

### Public Course Listing
```text
+--------------------------------------------------------------+
| Top Nav | Search | Categories | Language | Difficulty        |
+--------------------------------------------------------------+
| Hero: "Learn at the pace of ambition" + CTA                |
+--------------------------------------------------------------+
| Filter rail      | Course card grid                           |
| - Price          | [Thumbnail][Title][Instructor][Rating]     |
| - Duration       | [Price][Badge][Enroll CTA]                 |
| - Rating         | ...                                         |
+--------------------------------------------------------------+
```

### Course Learning Player
```text
+--------------------------------------------------------------+
| Video Player (watermark, speed, subtitles, notes, bookmarks) |
+-------------------------------+------------------------------+
| Current lesson content        | Course curriculum sidebar    |
| Transcript / Resources tabs   | Progress + next lesson       |
+-------------------------------+------------------------------+
```

### Instructor Dashboard
```text
+--------------------------------------------------------------+
| KPI Cards: Revenue | Enrollments | Completion | Refunds      |
+--------------------------------------------------------------+
| Left nav: Courses/Analytics/Payouts/Coupons/Messages         |
| Main: Course pipeline (Draft, Review, Published)             |
+--------------------------------------------------------------+
```

## 4. High-Fidelity Design Direction
- Theme name: Editorial-Tech Fusion.
- Visual language: warm neutral base + electric accent for action.
- Card style: soft elevation, strong typography hierarchy.
- Data-heavy surfaces: dense but readable tables/charts with sticky controls.

## 5. Component Library
- Foundations: color tokens, typography scale, spacing, elevation, radii.
- Navigation: top nav, side nav, breadcrumb, pagination.
- Discovery: search bar, filter chips, faceted filter panel, course cards.
- Learning: video player controls, transcript pane, note composer, progress ring.
- Live Sessions: session card (countdown to start / live now / ended), register button, join button (enabled only inside join window), attendance list, recording playback card.
- Commerce: pricing cards, order summary, payment selector, coupon input.
- Communication: chat thread list, message bubble, notification center.
- Admin: data table, moderation panel, audit timeline, role editor.
- Feedback: toasts, alerts, loaders, empty states.

## 6. Design System Tokens

### Color Palette
- Primary `#0B3A53` (Deep Atlantic)
- Secondary `#146C94` (Harbor Blue)
- Accent `#FF7A59` (Coral Signal)
- Success `#0F9D58`
- Warning `#F4B400`
- Error `#DB4437`
- Surface `#F7F5F2`
- Ink `#1E1E1E`

### Typography Guide
- Heading font: Sora (700/600)
- Body font: Source Sans 3 (400/500)
- Monospace: IBM Plex Mono
- Scale:
  - Display: 56/64
  - H1: 40/48
  - H2: 32/40
  - H3: 24/32
  - Body L: 18/28
  - Body M: 16/24
  - Body S: 14/20

### Spacing and Layout
- Base unit: 4px.
- Container widths: 1200px desktop, 100% fluid mobile.
- Grid: 12-col desktop, 8-col tablet, 4-col mobile.

## 7. Accessibility Standards
- Minimum contrast 4.5:1 for normal text.
- Keyboard-operable player controls and transcript navigation.
- Focus indicators visible on all interactive controls.
- Captions and transcripts mandatory for published video lessons.

## 8. SEO UI Requirements (Web)
- SSR pages for course/category/landing pages.
- Dynamic metadata and Open Graph image generation.
- Schema.org Course + FAQ + Breadcrumb JSON-LD.
