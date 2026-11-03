# Cohortly – Data Dictionary

This document provides a comprehensive data dictionary for all relational tables, entities, and data structures in **Cohortly – Learning Analytics & Cohort Intelligence Platform**.

---

## 1. `instructors`
Stores academic instructors and mentors delivering courses.

| Field Name | Type | Constraints | Description | Sample Value |
|---|---|---|---|---|
| `instructor_id` | VARCHAR(32) | PRIMARY KEY | Unique deterministic identifier | `INS-000001` |
| `first_name` | VARCHAR(64) | NOT NULL | Instructor's given name | `Elena` |
| `last_name` | VARCHAR(64) | NOT NULL | Instructor's family name | `Rostova` |
| `email` | VARCHAR(128) | NOT NULL, UNIQUE | Synthetic institutional email | `elena.rostova@cohortly.internal` |
| `department` | VARCHAR(64) | NOT NULL | Academic or training department | `AI Engineering` |
| `created_at` | TIMESTAMP | NOT NULL | Deterministic synthetic record creation time | `2026-08-01T00:00:00Z` |

---

## 2. `learners`
Stores enrolled students and learners.

| Field Name | Type | Constraints | Description | Sample Value |
|---|---|---|---|---|
| `learner_id` | VARCHAR(32) | PRIMARY KEY | Unique deterministic identifier | `LRN-000001` |
| `first_name` | VARCHAR(64) | NOT NULL | Learner's given name | `Marcus` |
| `last_name` | VARCHAR(64) | NOT NULL | Learner's family name | `Chen` |
| `email` | VARCHAR(128) | NOT NULL, UNIQUE | Synthetic learner contact email | `marcus.chen.1@synthetic.cohortly.io` |
| `registration_date` | DATE | NOT NULL | Calendar date learner joined platform | `2026-08-15` |
| `learner_status` | VARCHAR(20) | NOT NULL | Lifecycle state (`ACTIVE`, `INACTIVE`, `SUSPENDED`) | `ACTIVE` |
| `region` | VARCHAR(32) | NOT NULL | Geographic operational region | `North America` |
| `learning_mode` | VARCHAR(20) | NOT NULL | Modality (`SELF_PACED`, `COHORT_BASED`, `BLENDED`) | `COHORT_BASED` |
| `created_at` | TIMESTAMP | NOT NULL | Deterministic synthetic creation timestamp | `2026-08-15T09:30:00Z` |

---

## 3. `courses`
Stores academic courses and curriculums.

| Field Name | Type | Constraints | Description | Sample Value |
|---|---|---|---|---|
| `course_id` | VARCHAR(32) | PRIMARY KEY | Unique deterministic identifier | `CRS-000001` |
| `course_name` | VARCHAR(128) | NOT NULL | Full course title | `Distributed Systems with Python` |
| `category` | VARCHAR(64) | NOT NULL | Curricular category | `Cloud Computing` |
| `difficulty_level` | VARCHAR(20) | NOT NULL | Level (`BEGINNER`, `INTERMEDIATE`, `ADVANCED`) | `ADVANCED` |
| `instructor_id` | VARCHAR(32) | NOT NULL, FK -> `instructors.instructor_id` | Assigned lead instructor | `INS-000001` |
| `course_status` | VARCHAR(20) | NOT NULL | Course lifecycle (`ACTIVE`, `ARCHIVED`, `DRAFT`) | `ACTIVE` |
| `created_at` | TIMESTAMP | NOT NULL | Deterministic synthetic creation timestamp | `2026-08-01T00:00:00Z` |

---

## 4. `cohorts`
Groups learners into scheduled study batches with defined start and end dates.

| Field Name | Type | Constraints | Description | Sample Value |
|---|---|---|---|---|
| `cohort_id` | VARCHAR(32) | PRIMARY KEY | Unique deterministic identifier | `COH-2026-001` |
| `cohort_name` | VARCHAR(128) | NOT NULL | Program batch name | `Fall 2026 AI Immersion` |
| `start_date` | DATE | NOT NULL | Cohort commencement date | `2026-09-01` |
| `end_date` | DATE | NOT NULL | Cohort graduation date | `2026-12-15` |
| `region` | VARCHAR(32) | NOT NULL | Geographic operational hub | `North America` |
| `program_type` | VARCHAR(32) | NOT NULL | Delivery pace (`ACCELERATED`, `STANDARD`, `PART_TIME`) | `ACCELERATED` |
| `created_at` | TIMESTAMP | NOT NULL | Deterministic synthetic creation timestamp | `2026-08-15T00:00:00Z` |

---

## 5. `enrollments`
Binds learners to specific courses and cohorts.

| Field Name | Type | Constraints | Description | Sample Value |
|---|---|---|---|---|
| `enrollment_id` | VARCHAR(64) | PRIMARY KEY | Unique composite ID (`ENR-<learner_id>-<course_id>`) | `ENR-LRN-000001-CRS-000001` |
| `learner_id` | VARCHAR(32) | NOT NULL, FK -> `learners.learner_id` | Registered learner | `LRN-000001` |
| `course_id` | VARCHAR(32) | NOT NULL, FK -> `courses.course_id` | Enrolled course | `CRS-000001` |
| `cohort_id` | VARCHAR(32) | NOT NULL, FK -> `cohorts.cohort_id` | Assigned student cohort | `COH-2026-001` |
| `enrolled_at` | TIMESTAMP | NOT NULL | Moment of registration | `2026-09-01T10:00:00Z` |
| `enrollment_status` | VARCHAR(20) | NOT NULL | Status (`ACTIVE`, `COMPLETED`, `DROPPED`, `PAUSED`) | `ACTIVE` |
| `expected_completion_date` | DATE | NOT NULL | Scheduled target finish date | `2026-12-15` |
| `completed_at` | TIMESTAMP | NULL | Actual moment of completion | `2026-11-20T16:45:00Z` |
| `dropped_at` | TIMESTAMP | NULL | Moment of withdrawal (if dropped) | `NULL` |

*Constraint*: `UNIQUE(learner_id, course_id)` prevents accidental dual enrollments.

---

## 6. `content_items`
Stores hierarchical modules, lessons, and assets within a course.

| Field Name | Type | Constraints | Description | Sample Value |
|---|---|---|---|---|
| `content_id` | VARCHAR(64) | PRIMARY KEY | Unique composite ID (`CNT-<course_id>-<seq>`) | `CNT-CRS-000001-001` |
| `course_id` | VARCHAR(32) | NOT NULL, FK -> `courses.course_id` | Parent course | `CRS-000001` |
| `parent_content_id` | VARCHAR(64) | NULL, FK -> `content_items.content_id` | Self-reference for hierarchical modules/lessons | `NULL` (Module) or `CNT-...` (Lesson) |
| `title` | VARCHAR(128) | NOT NULL | Content unit title | `Introduction to Consensus Algorithms` |
| `content_type` | VARCHAR(20) | NOT NULL | Type (`VIDEO`, `ARTICLE`, `DOCUMENT`, `QUIZ`, `ASSIGNMENT`) | `VIDEO` |
| `sequence_number` | INTEGER | NOT NULL | Curricular ordering index (1, 2, 3...) | `1` |
| `estimated_duration_minutes` | INTEGER | NOT NULL | Estimated consumption time | `45` |
| `is_required` | BOOLEAN | NOT NULL, DEFAULT 1 | Whether required for completion | `1` |
| `created_at` | TIMESTAMP | NOT NULL | Deterministic synthetic creation timestamp | `2026-08-01T00:00:00Z` |

---

## 7. `activity_events`
Stores raw user interaction events, telemetry, and learning sessions.

| Field Name | Type | Constraints | Description | Sample Value |
|---|---|---|---|---|
| `event_id` | VARCHAR(96) | PRIMARY KEY | Unique deterministic event identifier: <br>• Normal: `EVT-<enrollment_id>-<seq>`<br>• Unenrolled: `EVT-UNENROLLED-<lrn>-<crs>-<seq>` | `EVT-ENR-LRN-000001-CRS-000001-000001` |
| `enrollment_id` | VARCHAR(64) | NULL, FK -> `enrollments.enrollment_id` | Associated enrollment (NULL for unenrolled anomaly) | `ENR-LRN-000001-CRS-000001` |
| `learner_id` | VARCHAR(32) | NOT NULL, FK -> `learners.learner_id` | Interacting learner | `LRN-000001` |
| `course_id` | VARCHAR(32) | NOT NULL, FK -> `courses.course_id` | Context course | `CRS-000001` |
| `content_id` | VARCHAR(64) | NULL, FK -> `content_items.content_id` | Target content item (if applicable) | `CNT-CRS-000001-001` |
| `event_type` | VARCHAR(32) | NOT NULL | Telemetry event type (`COURSE_OPENED`, `CONTENT_VIEWED`, `VIDEO_STARTED`, `VIDEO_PROGRESS`, `VIDEO_COMPLETED`, `DOCUMENT_DOWNLOADED`, `QUIZ_STARTED`, `QUIZ_SUBMITTED`, `LOGIN`, `COURSE_COMPLETED`) | `VIDEO_COMPLETED` |
| `event_timestamp_utc` | TIMESTAMP | NOT NULL | Moment of user action in UTC | `2026-09-02T14:30:15Z` |
| `source_timezone` | VARCHAR(64) | NOT NULL | Valid IANA timezone identifier | `America/New_York` |
| `event_date` | DATE | NOT NULL | Local calendar date in `source_timezone` | `2026-09-02` |
| `session_id` | VARCHAR(64) | NOT NULL | User session identifier | `SES-LRN-000001-20260902-1400` |
| `device_type` | VARCHAR(20) | NOT NULL | Device (`DESKTOP`, `MOBILE`, `TABLET`) | `DESKTOP` |
| `sync_status` | VARCHAR(20) | NOT NULL | Synchronization mode (`REALTIME`, `OFFLINE_SYNC`, `LATE_SYNC`) | `REALTIME` |
| `ingestion_timestamp` | TIMESTAMP | NOT NULL | Arrival time at backend server in UTC | `2026-09-02T14:30:16Z` |
| `idempotency_key` | VARCHAR(64) | NOT NULL | Deterministic SHA-256 hash for deduplication | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

---

## 8. `assessments`
Defines graded quizzes, exams, and projects for a course.

| Field Name | Type | Constraints | Description | Sample Value |
|---|---|---|---|---|
| `assessment_id` | VARCHAR(32) | PRIMARY KEY | Unique deterministic identifier | `ASM-2026-000001` |
| `course_id` | VARCHAR(32) | NOT NULL, FK -> `courses.course_id` | Parent course | `CRS-000001` |
| `title` | VARCHAR(128) | NOT NULL | Assessment title | `Consensus & Raft Midterm Exam` |
| `assessment_type` | VARCHAR(20) | NOT NULL | Format (`QUIZ`, `EXAM`, `PROJECT`, `PEER_REVIEW`) | `EXAM` |
| `max_score` | NUMERIC(5, 2) | NOT NULL, DEFAULT 100.00 | Maximum possible score | `100.00` |
| `passing_score` | NUMERIC(5, 2) | NOT NULL, DEFAULT 70.00 | Minimum required score to pass | `70.00` |
| `is_required` | BOOLEAN | NOT NULL, DEFAULT 1 | Whether required for course completion | `1` |
| `due_date` | DATE | NULL | Deadline for submission | `2026-10-31` |
| `created_at` | TIMESTAMP | NOT NULL | Deterministic synthetic creation timestamp | `2026-08-01T00:00:00Z` |

---

## 9. `attempts`
Records individual student assessment submissions.

| Field Name | Type | Constraints | Description | Sample Value |
|---|---|---|---|---|
| `attempt_id` | VARCHAR(64) | PRIMARY KEY | Unique composite ID (`ATT-<assessment_id>-<seq>`) | `ATT-ASM-2026-000001-000001` |
| `assessment_id` | VARCHAR(32) | NOT NULL, FK -> `assessments.assessment_id` | Target assessment | `ASM-2026-000001` |
| `enrollment_id` | VARCHAR(64) | NOT NULL, FK -> `enrollments.enrollment_id` | Submitting enrollment | `ENR-LRN-000001-CRS-000001` |
| `attempt_number` | INTEGER | NOT NULL | Sequential attempt counter (1, 2, ...) | `1` |
| `score` | NUMERIC(5, 2) | NULL | Achieved score (0.00 to `max_score`) | `85.50` |
| `submitted_at` | TIMESTAMP | NOT NULL | Moment of submission in UTC | `2026-10-15T18:20:00Z` |
| `graded_at` | TIMESTAMP | NULL | Moment of grading completion | `2026-10-15T18:20:05Z` |
| `attempt_status` | VARCHAR(20) | NOT NULL | Status (`IN_PROGRESS`, `SUBMITTED`, `GRADED`, `PASSED`, `FAILED`) | `PASSED` |

*Constraint*: `UNIQUE(enrollment_id, assessment_id, attempt_number)` ensures strictly sequential attempts.

---

## 10. `completion_rules`
Defines the governing graduation requirements for a course.

| Field Name | Type | Constraints | Description | Sample Value |
|---|---|---|---|---|
| `completion_rule_id` | VARCHAR(32) | PRIMARY KEY | Unique identifier (`CLR-<course_id>-V<ver>`) | `CLR-CRS-000001-V01` |
| `course_id` | VARCHAR(32) | NOT NULL, FK -> `courses.course_id` | Governed course | `CRS-000001` |
| `minimum_content_completion_percentage` | NUMERIC(5, 2) | NOT NULL, DEFAULT 80.00 | Threshold for content progress | `80.00` |
| `minimum_assessment_score` | NUMERIC(5, 2) | NOT NULL, DEFAULT 70.00 | Minimum average assessment score | `70.00` |
| `require_all_mandatory_assessments` | BOOLEAN | NOT NULL, DEFAULT 1 | If 1, all mandatory assessments must be passed | `1` |
| `effective_from` | DATE | NOT NULL | Rule effective start date | `2026-08-01` |
| `effective_to` | DATE | NULL | Rule expiration date (NULL if active) | `NULL` |
| `rule_version` | INTEGER | NOT NULL, DEFAULT 1 | Incremental rule version | `1` |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT 1 | Quick filter flag for active rule | `1` |

---

## 11. `course_outcomes`
Stores historical snapshots of student completion decisions and auditable rule evaluations.

| Field Name | Type | Constraints | Description | Sample Value |
|---|---|---|---|---|
| `outcome_id` | VARCHAR(96) | PRIMARY KEY | Unique snapshot ID (`OUT-<enr>-V<ver>`) | `OUT-ENR-LRN-000001-CRS-000001-V01` |
| `enrollment_id` | VARCHAR(64) | NOT NULL, FK -> `enrollments.enrollment_id` | Evaluated enrollment | `ENR-LRN-000001-CRS-000001` |
| `outcome_version` | INTEGER | NOT NULL, DEFAULT 1 | Snapshot version counter (1, 2, ...) | `1` |
| `completion_rule_id` | VARCHAR(32) | NOT NULL, FK -> `completion_rules.completion_rule_id` | Governing rule evaluated | `CLR-CRS-000001-V01` |
| `completion_status` | VARCHAR(20) | NOT NULL | Decision (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `INCOMPLETE`, `FAILED`) | `COMPLETED` |
| `content_completion_percentage` | NUMERIC(5, 2) | NOT NULL, DEFAULT 0.00 | Calculated content progress | `92.50` |
| `assessment_progress_percentage` | NUMERIC(5, 2) | NOT NULL, DEFAULT 0.00 | Calculated assessment progress | `100.00` |
| `final_assessment_score` | NUMERIC(5, 2) | NULL | Final weighted/average score | `84.50` |
| `calculated_at` | TIMESTAMP | NOT NULL | Moment of snapshot calculation | `2026-11-20T16:45:00Z` |
| `supersedes_outcome_id` | VARCHAR(96) | NULL, FK -> `course_outcomes.outcome_id` | Reference to previous snapshot version | `NULL` |
| `is_current` | BOOLEAN | NOT NULL, DEFAULT 1 | 1 for latest snapshot, 0 for history | `1` |
| `outcome_reason` | TEXT | NOT NULL | JSON checklist and narrative explanation | `{"content_passed": true, ...}` |

---

## 12. `exceptions`
Operational store of detected data quality issues and anomalies.

| Field Name | Type | Constraints | Description | Sample Value |
|---|---|---|---|---|
| `exception_id` | VARCHAR(32) | PRIMARY KEY | Unique identifier | `EXC-000001` |
| `issue_type` | VARCHAR(64) | NOT NULL | Issue classification (`DUPLICATE_ACTIVITY_EVENT`, `POTENTIAL_NEAR_DUPLICATE`, `UNENROLLED_LEARNER_ACTIVITY`, `PREMATURE_COMPLETION`, `TIMEZONE_DATE_MISMATCH`, etc.) | `UNENROLLED_LEARNER_ACTIVITY` |
| `severity` | VARCHAR(20) | NOT NULL | Priority level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) | `HIGH` |
| `entity_type` | VARCHAR(32) | NOT NULL | Target entity type (`ACTIVITY_EVENT`, `ENROLLMENT`, `COURSE_OUTCOME`, etc.) | `ACTIVITY_EVENT` |
| `entity_id` | VARCHAR(96) | NOT NULL | Primary key of affected record | `EVT-UNENROLLED-LRN-000042-CRS-000005-000001` |
| `detected_at` | TIMESTAMP | NOT NULL | Moment of detection in UTC | `2026-10-22T00:05:00Z` |
| `description` | TEXT | NOT NULL | Plain-English summary of the anomaly | `Activity logged by learner without course enrollment` |
| `evidence` | JSON | NOT NULL | Verifiable structured data snippet | `{"learner_id": "LRN-000042", "course_id": "CRS-000005", "enrollment_found": false}` |
| `relevant_rule` | VARCHAR(128) | NOT NULL | Business rule reference | `RULE-INTEGRITY-001: Enrollment Relationship Integrity` |
| `recommended_action` | TEXT | NOT NULL | Actionable advice for support/admin | `Verify enrollment ledger; create enrollment or invalidate event.` |
| `resolution_status` | VARCHAR(20) | NOT NULL, DEFAULT 'OPEN' | Workflow state (`OPEN`, `INVESTIGATING`, `RESOLVED`, `FALSE_POSITIVE`) | `OPEN` |
