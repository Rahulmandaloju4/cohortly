# Cohortly – Business Rules & Compliance Specification

This document details the governing business rules, compliance checks, lifecycle invariants, and exception classification logic implemented across **Cohortly**.

---

## 1. Course Completion & Graduation Decision Rules

### RULE-COMPL-001: Completion Eligibility
An enrollment may be marked with `completion_status = 'COMPLETED'` **if and only if** all four conditions are met under the active completion rule (`completion_rules`):
1. **Content Threshold**: Calculated `content_completion_percentage` $\ge$ `minimum_content_completion_percentage` (default 80.00%).
2. **Assessment Threshold**: Calculated `final_assessment_score` $\ge$ `minimum_assessment_score` (default 70.00%).
3. **Mandatory Assessments Passed**: If `require_all_mandatory_assessments = 1`, every assessment with `is_required = 1` must have at least one graded attempt where `score >= passing_score`.
4. **Lifecycle Order**: The enrollment must be in `ACTIVE` status prior to completion and `completed_at >= enrolled_at`.

### RULE-COMPL-002: Incomplete & Drop Statuses
- If a course end date has elapsed and completion criteria are not met, the status transitions to `INCOMPLETE` or `FAILED`.
- If a student withdraws, status is set to `DROPPED` with `dropped_at` timestamp populated.

### RULE-COMPL-003: Outcome Snapshot Versioning
Recalculating completion status must never overwrite existing rows:
- Existing current outcome has `is_current` set to `0`.
- A new record is inserted with `outcome_version = previous_version + 1`, `supersedes_outcome_id = previous_id`, and `calculated_at` recorded.
- The `outcome_reason` field must contain a structured JSON breakdown of all tested rules.

---

## 2. Event Ingestion, Deduplication & Lifecycle Rules

### RULE-EVENT-001: Exact Deduplication
- Multiple events with identical `idempotency_key` are detected.
- The record with the earliest `ingestion_timestamp` (or lowest `event_id` tie-breaker) is canonical.
- All non-canonical exact duplicates are marked `is_exact_duplicate = 1` and excluded from analytics calculations.

### RULE-EVENT-002: Potential Near-Duplicate Classification
- Events from the same `(learner_id, course_id, content_id, event_type, session_id)` occurring within $|t_1 - t_2| \le 5.0\text{ seconds}$ are flagged as `potential_near_duplicate`.
- **Analytics Inclusion Policy**: They are **NOT** automatically excluded from engagement metrics; they remain active in engagement analytics as candidates for investigation, preventing false negatives on rapid legitimate interactions (e.g. video scrub, rapid next clicks). They are cataloged in the exceptions ledger for investigator review and only removed if explicitly resolved as `CONFIRMED_DUPLICATE`.

### RULE-EVENT-003: Ingestion vs Occurrence Timing
- `ingestion_timestamp >= event_timestamp_utc` must always hold.
- Offline and mobile synchronizations can result in large latency ($\Delta t = \text{ingestion} - \text{occurrence} > 0$), which is legitimate under `sync_status IN ('OFFLINE_SYNC', 'LATE_SYNC')`.

### RULE-EVENT-004: Post-Completion Activity
- Activity occurring after `enrollment.completed_at` is classified as legitimate post-completion review.
- It is excluded from completion-rule requirements but tracked in lifelong learning analytics.

### RULE-STATE-001: Append-Only State Transition History
- Every lifecycle state transition must create an immutable record in `state_history`:
  - Enrollment transitions (`ACTIVE` -> `COMPLETED`, `ACTIVE` -> `DROPPED`, `ACTIVE` -> `PAUSED`).
  - Exception resolution transitions (`OPEN` -> `INVESTIGATING` -> `RESOLVED` / `FALSE_POSITIVE`).
  - Outcome calculation transitions.
- Records in `state_history` must **never** be overwritten or deleted.
- Current-state columns (`enrollments.enrollment_status`, `exceptions.resolution_status`) are maintained simultaneously for indexed query performance.

---

## 3. Cross-Entity Relational Integrity Rules

### RULE-INTEG-001: Event-Enrollment Match
If `activity_events.enrollment_id` is NOT NULL:
- `activity_events.learner_id == enrollments.learner_id`
- `activity_events.course_id == enrollments.course_id`

### RULE-INTEG-002: Content-Course Match
If `activity_events.content_id` is NOT NULL:
- `content_items.course_id == activity_events.course_id`

### RULE-INTEG-003: Attempt-Enrollment Match
For every assessment attempt in `attempts`:
- `assessments.course_id == enrollments.course_id`

### RULE-INTEG-004: Outcome-Rule Match
For every outcome in `course_outcomes`:
- `completion_rules.course_id == enrollments.course_id`

### RULE-INTEG-005: Content Tree Consistency
For child content units:
- `child.course_id == parent.course_id`

---

## 4. Operational Anomaly Detection Rules

The anomaly detection engine enforces four core rules via pure relational SQL checks without access to ground truth:

### ANOMALY-001: Duplicate Activity Events
- **Detection Query**: `SELECT idempotency_key, COUNT(*) FROM activity_events GROUP BY idempotency_key HAVING COUNT(*) > 1;`
- **Severity**: MEDIUM.
- **Recommended Action**: Flag redundant rows; preserve earliest canonical record in analytics view.

### ANOMALY-002: Unenrolled Learner Activity
- **Detection Query**: `SELECT event_id FROM activity_events e WHERE e.enrollment_id IS NULL OR NOT EXISTS (SELECT 1 FROM enrollments en WHERE en.learner_id = e.learner_id AND en.course_id = e.course_id);`
- **Severity**: HIGH.
- **Recommended Action**: Audit authentication middleware; check if student was dropped or unregistered; enroll or void event.

### ANOMALY-003: Premature Completion Rule Violation
- **Detection Query**: Evaluates current `course_outcomes` where `completion_status = 'COMPLETED'` against actual student progress. Flags outcomes where content completion $< 80\%$ or any mandatory assessment is failed/missing.
- **Severity**: CRITICAL.
- **Recommended Action**: Revoke graduation badge; recalculate outcome snapshot to `IN_PROGRESS`; notify student of missing requirements.

### ANOMALY-004: Timezone Date Mismatch
- **Detection Query**: Compares stored `event_date` to `DATE(timezone_convert(event_timestamp_utc, source_timezone))`.
- **Severity**: LOW.
- **Recommended Action**: Re-derive local date from UTC timestamp and IANA timezone; repair client telemetry clock.

---

## 5. Role-Based Access Control (RBAC) Rules

Cohortly recognizes 5 primary roles:

| Role | Access Scope | Write / Action Permissions |
|---|---|---|
| **`LEARNER`** | Read self progress, enrollments, attempts, content checklist | Submit attempts, log activity |
| **`INSTRUCTOR`** | Read assigned courses, enrolled students, content drop-offs | Grade attempts, review course analytics |
| **`ACADEMIC_ADMIN`** | Read all cohorts, courses, curriculum outcomes, retention | Export analytics, compare cohorts |
| **`SUPPORT_STAFF`** | Read learner issues, inactive learners, anomaly alerts | Triage exceptions (`INVESTIGATING`, `RESOLVED`, `FALSE_POSITIVE`) |
| **`PLATFORM_ADMIN`** | Unrestricted system-wide access | Run synthetic generator, run validation audit, manage schemas |

- **Header Contract**: Client requests transmit role context via `X-Demo-Role` (e.g. `LEARNER`, `INSTRUCTOR`, `ACADEMIC_ADMIN`, `SUPPORT_STAFF`, `PLATFORM_ADMIN`).
- **Authorization Enforcement**: FastAPI dependencies verify permissions per route and raise `HTTP 403 Forbidden` on violations.

> [!CAUTION]
> **Demonstration Architecture Disclaimer & Limitations**:
> `X-Demo-Role` is strictly a demonstration mechanism allowing evaluation of multi-persona views and server-side RBAC validation without requiring complex external OAuth/SSO credentials in an offline coding challenge.
> - **Limitations**: It does NOT provide cryptographic signature verification, session token issuance, password salting, or token revocation.
> - **Production Roadmap**: In a production enterprise deployment, `X-Demo-Role` must be replaced by OAuth2 / OpenID Connect (OIDC) Bearer JWT tokens, signed by an identity provider (e.g., Okta, Auth0, or Keycloak) with role claims verified cryptographically.
