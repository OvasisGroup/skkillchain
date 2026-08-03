// Mirrors the shapes actually returned by the Django/DRF backend
// (see backend/apps/*/serializers.py and docs/03-api/02-openapi.yaml).

export interface Profile {
  first_name: string;
  last_name: string;
  bio: string;
  // Read-only here — written only via uploadAvatar() (POST /auth/me/avatar/),
  // never through updateMe()'s JSON body.
  avatar: string | null;
  locale: string;
  timezone: string;
  linkedin_url: string;
  twitter_url: string;
  github_url: string;
  youtube_url: string;
  website_url: string;
}

// The 11 platform roles seeded in
// backend/apps/authorization/migrations/0002_seed_platform_roles.py.
// "guest" never appears in Me.roles — it's the unauthenticated default.
export type RoleCode =
  | "student"
  | "instructor"
  | "organization"
  | "affiliate"
  | "moderator"
  | "support_agent"
  | "finance_officer"
  | "content_reviewer"
  | "administrator"
  | "super_administrator";

export interface Me {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
  profile: Profile;
  roles: RoleCode[];
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface MfaChallenge {
  mfa_required: true;
  mfa_token: string;
}

export type LoginResult = TokenPair | MfaChallenge;

export interface Instructor {
  id: string;
  email: string;
}

export interface Course {
  id: string;
  title: string;
  slug: string;
  summary: string;
  instructor: Instructor;
  cover_image: string | null;
  price_amount: string;
  currency: string;
  language: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  status: string;
  published_at: string | null;
}

export interface CursorPage<T> {
  next: string | null;
  previous: string | null;
  results: T[];
}

// Public instructor directory (GET /instructors/, /instructors/{id}/) —
// "instructor" here means "owns at least one published course", not just
// holding the instructor role (see apps/catalog/views.py's
// _instructor_queryset for why).
export interface InstructorSummary {
  id: string;
  email: string;
  profile: Profile;
  published_course_count: number;
  // Distinct categories across this instructor's published courses — can
  // be empty even for an instructor with courses, since a course's
  // category is optional.
  categories: Category[];
}

export interface InstructorDetail extends InstructorSummary {
  courses: Course[];
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  parent: string | null;
}

export interface Tag {
  id: string;
  name: string;
  slug: string;
}

// Shape returned by the instructor create/update endpoint (CourseWriteSerializer) —
// narrower than Course/CourseDetail: no nested `instructor` object (category/tags
// come back as bare ids), and there's no created_at/updated_at/published_at.
// prerequisites/learning_objectives are write-only on this serializer, so they're
// never present in the response even though they can be submitted on create.
export interface CourseWriteResult {
  id: string;
  slug: string;
  status: string;
  title: string;
  summary: string;
  description: string;
  cover_image: string | null;
  language: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  price_amount: string;
  currency: string;
  // Nullable for older/directly seeded courses that predate the category
  // requirement — see CourseDetail.category above.
  category_id: string | null;
  tag_ids: string[];
}

export interface CourseDetail {
  id: string;
  title: string;
  slug: string;
  summary: string;
  description: string;
  instructor: Instructor;
  cover_image: string | null;
  price_amount: string;
  currency: string;
  language: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  status: string;
  rejection_reason: string;
  published_at: string | null;
  // Nullable: category is required for newly-created courses (the
  // instructor course-creation form enforces it), but older/directly
  // seeded courses can predate that requirement.
  category: Category | null;
  tags: Tag[];
  prerequisites: string[];
  learning_objectives: string[];
  created_at: string;
  updated_at: string;
}

export interface PreviewLesson {
  id: string;
  title: string;
  duration_seconds: number;
}

export interface PreviewSection {
  section: string;
  lessons: PreviewLesson[];
}

export interface Enrollment {
  id: string;
  course: Course;
  source: string;
  status: string;
  enrolled_at: string;
  completed_at: string | null;
}

// RFC 7807 problem+json — see backend/shared/api/exceptions.py.
export interface ProblemDetail {
  type: string;
  title: string;
  status: number;
  detail?: string;
  errors?: Record<string, string[]> | string[] | string;
}

export function isMfaChallenge(result: LoginResult): result is MfaChallenge {
  return "mfa_required" in result;
}

// ---------------------------------------------------------------------------
// Student dashboard
// ---------------------------------------------------------------------------

export interface CourseSummary {
  id: string;
  title: string;
  slug: string;
  summary: string;
}

export interface ProgressEntry {
  lesson_id: string;
  lesson_title: string;
  percent_complete: number;
  last_position_seconds: number;
  last_viewed_at: string;
}

export interface EnrollmentProgress {
  enrollment_id: string;
  status: string;
  overall_percent: number;
  lessons: ProgressEntry[];
}

export interface WishlistItem {
  course: CourseSummary;
  added_at: string;
}

export interface Notification {
  id: string;
  type: string;
  channel: string;
  title: string;
  body: string;
  read_at: string | null;
  sent_at: string | null;
  created_at: string;
}

export interface Certificate {
  id: string;
  certificate_uid: string;
  course: CourseSummary;
  qr_payload: string;
  pdf_file: string | null;
  issued_at: string;
}

export type GradeEntry =
  | {
      type: "quiz";
      id: string;
      title: string;
      score: number | null;
      passed: boolean | null;
      submitted_at: string | null;
    }
  | {
      type: "assignment";
      id: string;
      title: string;
      grade: number | null;
      graded_at: string | null;
    };

// ---------------------------------------------------------------------------
// Instructor dashboard
// ---------------------------------------------------------------------------

export interface Wallet {
  id: string | null;
  balance_amount: string;
  currency: string;
}

export interface Payout {
  id: string;
  period_start: string;
  period_end: string;
  amount_gross: string;
  amount_net: string;
  status: "pending" | "paid" | "failed";
  paid_at: string | null;
  created_at: string;
}

export interface EarningsAggregate {
  period_start: string;
  period_end: string;
  currency: string;
  gross_amount: string;
  net_amount: string;
}

export interface Assignment {
  id: string;
  course: string;
  title: string;
  instructions: string;
  due_policy: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Curriculum authoring (sections, lessons, quizzes, coding exercises)
// ---------------------------------------------------------------------------

export type LessonType = "video" | "pdf" | "article" | "quiz" | "assignment";

export interface Section {
  id: string;
  title: string;
  sort_order: number;
}

export interface Lesson {
  id: string;
  title: string;
  lesson_type: LessonType;
  sort_order: number;
  duration_seconds: number;
  is_preview: boolean;
  // Only present for video/pdf lessons; absent for article/quiz/assignment.
  content_file?: string | null;
}

// ---------------------------------------------------------------------------
// Student-facing curriculum + lesson content
// ---------------------------------------------------------------------------

export interface CurriculumLesson {
  id: string;
  title: string;
  lesson_type: LessonType;
  sort_order: number;
  duration_seconds: number;
  is_preview: boolean;
}

export interface CurriculumSection {
  id: string;
  title: string;
  sort_order: number;
  lessons: CurriculumLesson[];
}

export interface LessonContent {
  id: string;
  title: string;
  lesson_type: LessonType;
  duration_seconds: number;
  content_file: string | null;
}

export interface ProgressUpdateInput {
  lesson_id: string;
  percent_complete: number;
  last_position_seconds?: number;
}

export interface AnswerInput {
  text: string;
  is_correct: boolean;
  sort_order: number;
}

export interface QuestionInput {
  type: "single_choice" | "multiple_choice";
  prompt: string;
  explanation?: string;
  sort_order: number;
  answers: AnswerInput[];
}

export interface QuizCreateInput {
  title: string;
  attempts_allowed?: number;
  pass_score?: number;
  section?: string | null;
  questions?: QuestionInput[];
}

export interface Answer {
  id: string;
  text: string;
  sort_order: number;
}

export interface Question {
  id: string;
  type: "single_choice" | "multiple_choice";
  prompt: string;
  sort_order: number;
  answers: Answer[];
}

export interface QuizDetail {
  id: string;
  title: string;
  attempts_allowed: number;
  pass_score: number;
  questions: Question[];
}

export interface AssignmentCreateInput {
  title: string;
  instructions: string;
  due_policy?: Record<string, unknown>;
}

export interface TestCaseInput {
  input?: string;
  expected_output: string;
  is_hidden: boolean;
  weight: number;
}

export interface CodingExerciseCreateInput {
  title: string;
  prompt: string;
  starter_code?: string;
  language?: "python";
  time_limit_ms?: number;
  memory_limit_mb?: number;
  section?: string | null;
  test_cases: TestCaseInput[];
}

export interface CodingExerciseDetail {
  id: string;
  title: string;
  prompt: string;
  starter_code: string;
  language: string;
  time_limit_ms: number;
  memory_limit_mb: number;
}

export interface AssignmentSubmission {
  id: string;
  assignment: string;
  student_email: string;
  content_ref: string;
  grade: number | null;
  feedback: string;
  graded_at: string | null;
  submitted_at: string;
  ai_suggested_grade: number | null;
  ai_suggested_feedback: string;
  ai_suggested_at: string | null;
}

export interface AssignmentGradeRequest {
  grade: number;
  feedback?: string;
}

// ---------------------------------------------------------------------------
// Moderator / content reviewer
// ---------------------------------------------------------------------------

export interface InstructorApplication {
  id: string;
  user: string;
  user_email: string;
  status: "pending" | "approved";
  applied_at: string;
  approved_at: string | null;
  approved_by: string | null;
}

export interface NotificationTemplate {
  id: string;
  code: string;
  channel: "email" | "sms" | "push";
  locale: string;
  subject_template: string;
  body_template: string;
  is_active: boolean;
}

export interface EmailTemplate {
  id: string;
  code: string;
  locale: string;
  subject: string;
  html_body: string;
  text_body: string;
  is_active: boolean;
}

// ---------------------------------------------------------------------------
// Support agent
// ---------------------------------------------------------------------------

export interface SupportTicket {
  id: string;
  requester: string;
  assignee: string | null;
  category: "billing" | "technical" | "course_content" | "other";
  priority: "low" | "normal" | "high" | "urgent";
  status: "open" | "in_progress" | "resolved" | "closed";
  subject: string;
  is_sla_breached: boolean;
  created_at: string;
  updated_at: string;
}

export interface SupportTicketMessage {
  id: string;
  ticket: string;
  sender: string;
  body: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Finance officer
// ---------------------------------------------------------------------------

export interface RevenueDailyAggregate {
  period_start: string;
  period_end: string;
  currency: string;
  gross_amount: string;
  net_amount: string;
}

export interface Coupon {
  id: string;
  code: string;
  discount_type: "percent" | "fixed";
  discount_value: string;
  valid_from: string | null;
  valid_to: string | null;
  usage_limit: number | null;
  per_user_limit: number | null;
  promotion: string | null;
  course: string | null;
}

export interface Promotion {
  id: string;
  name: string;
  campaign_type: string;
  banner_asset_key: string;
  starts_at: string | null;
  ends_at: string | null;
  status: "draft" | "active" | "ended";
}

// ---------------------------------------------------------------------------
// Affiliate
// ---------------------------------------------------------------------------

export interface AffiliateAccount {
  id: string;
  referral_code: string;
  commission_rate: string;
}

export interface AffiliateReferral {
  id: string;
  referred_user_email: string;
  order: string;
  status: "pending" | "converted";
  created_at: string;
}

export interface AffiliateCommission {
  id: string;
  referral: string;
  commission_amount: string;
  payout_status: "pending" | "paid";
  created_at: string;
}

// ---------------------------------------------------------------------------
// Administrator
// ---------------------------------------------------------------------------

export interface AdminUser {
  id: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  created_at: string;
}

export interface AuditLog {
  id: string;
  actor: string | null;
  actor_email: string;
  action: string;
  entity_type: string;
  entity_id: string;
  ip_address: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Commerce
// ---------------------------------------------------------------------------

export interface OrderItem {
  id: string;
  item_type: "course" | "subscription_plan";
  item_id: string;
  unit_price: string;
  quantity: number;
}

export interface Order {
  id: string;
  status: "pending" | "paid" | "canceled" | "refunded";
  subtotal_amount: string;
  discount_amount: string;
  tax_amount: string;
  gift_card_amount: string;
  total_amount: string;
  currency: string;
  items: OrderItem[];
  created_at: string;
}

export type PaymentProviderCode = "stripe" | "paypal" | "flutterwave" | "paystack" | "mpesa";

export interface Payment {
  id: string;
  order: string;
  provider: string;
  provider_payment_id: string;
  status: "pending" | "succeeded" | "failed" | "refunded";
  amount: string;
  currency: string;
  paid_at: string | null;
}

export interface PayResponse {
  payment: Payment;
  client_secret: string | null;
  redirect_url: string | null;
}

export interface Setting {
  id: string;
  scope_type: "platform";
  scope_id: string | null;
  key: string;
  value_json: unknown;
  updated_at: string;
}

export type ConferencingProvider = "zoom" | "google_meet";

export interface ConferencingAccount {
  id: string;
  provider: ConferencingProvider;
  external_account_id: string;
  connected_at: string;
  revoked_at: string | null;
}

export type LiveSessionStatus = "scheduled" | "live" | "ended" | "canceled";

export interface LiveSession {
  id: string;
  course: string | null;
  provider: ConferencingProvider;
  title: string;
  description: string;
  scheduled_start_at: string;
  scheduled_end_at: string;
  timezone: string;
  status: LiveSessionStatus;
  capacity: number | null;
  is_recorded: boolean;
}

export interface LiveSessionCreateInput {
  conferencing_account_id: string;
  provider: ConferencingProvider;
  title: string;
  description?: string;
  scheduled_start_at: string;
  scheduled_end_at: string;
  timezone?: string;
  capacity?: number;
  is_recorded?: boolean;
}

export interface LiveSessionUpdateInput {
  title?: string;
  description?: string;
  scheduled_start_at?: string;
  scheduled_end_at?: string;
  timezone?: string;
  capacity?: number;
}

export type LiveSessionRegistrationStatus = "registered" | "attended" | "no_show" | "canceled";

export interface LiveSessionRegistration {
  id: string;
  student_email: string;
  status: LiveSessionRegistrationStatus;
  registered_at: string;
  joined_at: string | null;
  left_at: string | null;
  attended_duration_seconds: number;
}

export interface LiveSessionRecording {
  playback_url: string;
  duration_seconds: number;
  available_at: string | null;
}

export interface DiscussionPost {
  id: string;
  course: string;
  user: string;
  user_email: string;
  body: string;
  created_at: string;
}
