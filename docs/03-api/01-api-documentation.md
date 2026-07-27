# API Documentation (REST + WebSocket)

## 1. API Standards
- Base URL: `/api/v1`
- Auth: `Authorization: Bearer <JWT>`
- Idempotency: `Idempotency-Key` required for checkout and webhook-sensitive actions.
- Pagination: cursor-based for large collections.
- Errors: RFC7807 problem+json structure.

## 2. Authentication APIs
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/token/refresh`
- `POST /auth/logout`
- `POST /auth/mfa/enroll`
- `POST /auth/mfa/verify`
- `POST /auth/mfa/login-verify` — completes a login that returned `mfa_required: true`
- `POST /auth/oauth/{provider}/token` — client performs the OAuth flow with the provider's own SDK (Google Sign-In, Sign in with Apple, Facebook Login) and exchanges the resulting token here, rather than a server-driven redirect; see [Core Flows §8](../04-platform-structure/02-core-flows.md#8-oauth-social-login-flow) for why, given this platform serves both a web and a native mobile client
- `GET /auth/me`
- `PATCH /auth/me`

## 3. Course Catalog APIs
- `GET /courses`
- `GET /courses/{course_id}`
- `GET /courses/{course_id}/preview`
- `GET /categories`
- `GET /tags`
- `GET /search/courses`

## 4. Instructor Content Management APIs
- `POST /instructor/courses`
- `PATCH /instructor/courses/{course_id}`
- `POST /instructor/courses/{course_id}/submit-review`
- `POST /instructor/courses/{course_id}/publish`
- `POST /instructor/courses/{course_id}/sections`
- `POST /instructor/sections/{section_id}/lessons`
- `POST /instructor/lessons/{lesson_id}/videos/upload-init`
- `POST /instructor/lessons/{lesson_id}/resources`
- `POST /instructor/courses/{course_id}/quizzes`
- `POST /instructor/courses/{course_id}/assignments`
- `POST /instructor/courses/{course_id}/coupons`
- `GET /instructor/dashboard/revenue`
- `GET /instructor/dashboard/analytics`
- `POST /instructor/payout-requests`

## 5. Student Learning APIs
- `POST /enrollments`
- `GET /students/me/courses`
- `GET /students/me/continue-learning`
- `GET /students/me/wishlist`
- `POST /students/me/wishlist/{course_id}`
- `DELETE /students/me/wishlist/{course_id}`
- `POST /progress`
- `GET /progress/{enrollment_id}`
- `POST /lesson-notes`
- `POST /bookmarks`
- `GET /certificates`
- `GET /certificates/{certificate_uid}/verify`

## 6. Live Session APIs
- `POST /instructor/conferencing-accounts/connect/{provider}`
- `GET /instructor/conferencing-accounts`
- `DELETE /instructor/conferencing-accounts/{account_id}`
- `POST /instructor/courses/{course_id}/live-sessions`
- `PATCH /instructor/live-sessions/{live_session_id}`
- `POST /instructor/live-sessions/{live_session_id}/cancel`
- `GET /instructor/live-sessions/{live_session_id}/registrations`
- `GET /courses/{course_id}/live-sessions`
- `GET /students/me/live-sessions`
- `POST /live-sessions/{live_session_id}/register`
- `DELETE /live-sessions/{live_session_id}/register`
- `GET /live-sessions/{live_session_id}/join`
- `GET /live-sessions/{live_session_id}/recording`

## 7. Assessment APIs
- `GET /quizzes/{quiz_id}`
- `POST /quizzes/{quiz_id}/attempts`
- `POST /quizzes/{quiz_id}/submit`
- `POST /assignments/{assignment_id}/submissions`
- `GET /students/me/grades`
- `GET /coding-exercises/{exercise_id}`
- `POST /coding-exercises/{exercise_id}/submissions`
- `GET /coding-exercises/{exercise_id}/submissions/{submission_id}`

## 8. Commerce APIs
- `POST /checkout/orders`
- `POST /checkout/orders/{order_id}/apply-coupon`
- `POST /checkout/orders/{order_id}/pay`
- `GET /payments`
- `GET /invoices`
- `POST /refunds`
- `GET /subscriptions`
- `POST /subscriptions`
- `PATCH /subscriptions/{subscription_id}/cancel`
- `GET /plans`
- `GET /gift-cards/{code}`
- `POST /checkout/orders/{order_id}/apply-gift-card`

## 9. Messaging and Notification APIs
- `GET /threads`
- `POST /threads`
- `GET /threads/{thread_id}/messages`
- `POST /threads/{thread_id}/messages`
- `GET /notifications`
- `POST /notifications/mark-read`

## 10. Review and Community APIs
- `GET /courses/{course_id}/reviews`
- `POST /courses/{course_id}/reviews`
- `PATCH /reviews/{review_id}`
- `DELETE /reviews/{review_id}`
- `GET /courses/{course_id}/discussions`
- `POST /courses/{course_id}/discussions`

## 11. Admin APIs
- `GET /admin/users`
- `PATCH /admin/users/{user_id}/status`
- `GET /admin/instructors`
- `POST /admin/instructors/{user_id}/approve`
- `GET /admin/courses/pending-review`
- `POST /admin/courses/{course_id}/approve`
- `POST /admin/courses/{course_id}/reject`
- `GET /admin/reports/revenue`
- `GET /admin/reports/engagement`
- `GET /admin/audit-logs`
- `GET /admin/support-tickets`
- `PATCH /admin/support-tickets/{ticket_id}`
- `GET /admin/settings`
- `PATCH /admin/settings`
- `GET /admin/coupons`
- `POST /admin/coupons`
- `GET /admin/promotions`
- `POST /admin/promotions`
- `PATCH /admin/promotions/{promotion_id}`
- `GET /admin/email-templates`
- `PATCH /admin/email-templates/{template_code}`
- `GET /admin/notification-templates`
- `PATCH /admin/notification-templates/{template_code}`

## 12. Analytics APIs
- `GET /analytics/revenue`
- `GET /analytics/course-performance`
- `GET /analytics/student-engagement`
- `GET /analytics/completion`
- `GET /analytics/watch-time`
- `GET /analytics/drop-off`
- `GET /analytics/instructor-earnings`

## 13. AI APIs
- `POST /ai/tutor/sessions`
- `POST /ai/tutor/sessions/{session_id}/messages`
- `POST /ai/courses/{course_id}/generate-quiz`
- `POST /ai/lessons/{lesson_id}/generate-summary`
- `POST /ai/lessons/{lesson_id}/generate-flashcards`
- `GET /students/me/flashcards`
- `POST /ai/videos/{video_id}/generate-transcript`
- `POST /ai/videos/{video_id}/generate-subtitles`
- `POST /ai/assignments/{submission_id}/grade`
- `GET /ai/recommendations/courses`
- `GET /ai/recommendations/learning-paths`
- `GET /ai/search`

## 14. Webhook APIs
- `POST /webhooks/stripe`
- `POST /webhooks/paypal`
- `POST /webhooks/flutterwave`
- `POST /webhooks/paystack`
- `POST /webhooks/mpesa`
- `POST /webhooks/video/{provider}`
- `POST /webhooks/zoom`
- `POST /webhooks/google-meet` (Google Calendar push notification channel; used to detect meeting end and Drive recording availability — polling fallback since Meet has no direct recording-ready webhook)

## 15. WebSocket Channels
- `ws://.../ws/notifications`
- `ws://.../ws/chat/{thread_id}`
- `ws://.../ws/course/{course_id}/discussion`
- `ws://.../ws/instructor/{instructor_id}/dashboard`
- `ws://.../ws/live-sessions/{live_session_id}` (live status: starting-soon, live, ended)

## 16. Search and Filtering
Query capabilities for `GET /search/courses`:
- text, category, tag, instructor_id, language, difficulty, rating_min, rating_max, price_min, price_max, duration_min, duration_max, has_certificate, is_subtitle_available, sort_by.

## 17. Response Contracts (Examples)

### Course list response
```json
{
  "items": [
    {
      "id": "crs_123",
      "title": "Advanced Django at Scale",
      "instructor": { "id": "usr_i1", "name": "Jane Doe" },
      "price": { "amount": "49.00", "currency": "USD" },
      "rating": 4.8,
      "duration_seconds": 31200,
      "language": "en",
      "difficulty": "advanced"
    }
  ],
  "next_cursor": "eyJpZCI6ImNyc18xMjMifQ"
}
```

### Error response
```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation failed",
  "status": 422,
  "detail": "coupon code expired",
  "trace_id": "b8f6fce8d5"
}
```
