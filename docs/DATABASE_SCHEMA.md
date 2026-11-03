# Cohortly – Database Schema & Relational Architecture

This document specifies the complete relational schema, table definitions, foreign key relationships, indexes, and SQLite configuration directives for **Cohortly**.

---

## 1. Engine Configuration & Pragmas

To guarantee high-throughput bulk ingestion (supporting 2,000,000 events) and immediate consistency on local SQLite storage, Cohortly initializes database connections with the following pragmas:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000; -- 64 MB memory page cache
PRAGMA temp_store = MEMORY;
PRAGMA busy_timeout = 10000;
```

---

## 2. Table Definitions (DDL)

```sql
-- 1. Instructors
CREATE TABLE IF NOT EXISTS instructors (
    instructor_id VARCHAR(32) PRIMARY KEY,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    email VARCHAR(128) NOT NULL UNIQUE,
    department VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

-- 2. Learners
CREATE TABLE IF NOT EXISTS learners (
    learner_id VARCHAR(32) PRIMARY KEY,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    email VARCHAR(128) NOT NULL UNIQUE,
    registration_date DATE NOT NULL,
    learner_status VARCHAR(20) NOT NULL CHECK (learner_status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')),
    region VARCHAR(32) NOT NULL,
    learning_mode VARCHAR(20) NOT NULL CHECK (learning_mode IN ('SELF_PACED', 'COHORT_BASED', 'BLENDED')),
    created_at TIMESTAMP NOT NULL
);

-- 3. Courses
CREATE TABLE IF NOT EXISTS courses (
    course_id VARCHAR(32) PRIMARY KEY,
    course_name VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL,
    difficulty_level VARCHAR(20) NOT NULL CHECK (difficulty_level IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')),
    instructor_id VARCHAR(32) NOT NULL REFERENCES instructors(instructor_id) ON DELETE RESTRICT,
    course_status VARCHAR(20) NOT NULL CHECK (course_status IN ('ACTIVE', 'ARCHIVED', 'DRAFT')),
    created_at TIMESTAMP NOT NULL
);

-- 4. Cohorts
CREATE TABLE IF NOT EXISTS cohorts (
    cohort_id VARCHAR(32) PRIMARY KEY,
    cohort_name VARCHAR(128) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    region VARCHAR(32) NOT NULL,
    program_type VARCHAR(32) NOT NULL CHECK (program_type IN ('ACCELERATED', 'STANDARD', 'PART_TIME')),
    created_at TIMESTAMP NOT NULL
);

-- 5. Enrollments
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id VARCHAR(64) PRIMARY KEY,
    learner_id VARCHAR(32) NOT NULL REFERENCES learners(learner_id) ON DELETE RESTRICT,
    course_id VARCHAR(32) NOT NULL REFERENCES courses(course_id) ON DELETE RESTRICT,
    cohort_id VARCHAR(32) NOT NULL REFERENCES cohorts(cohort_id) ON DELETE RESTRICT,
    enrolled_at TIMESTAMP NOT NULL,
    enrollment_status VARCHAR(20) NOT NULL CHECK (enrollment_status IN ('ACTIVE', 'COMPLETED', 'DROPPED', 'PAUSED')),
    expected_completion_date DATE NOT NULL,
    completed_at TIMESTAMP NULL,
    dropped_at TIMESTAMP NULL,
    CONSTRAINT uq_learner_course UNIQUE (learner_id, course_id)
);

-- 6. Content Items (Hierarchical Parent-Child Structure)
CREATE TABLE IF NOT EXISTS content_items (
    content_id VARCHAR(64) PRIMARY KEY,
    course_id VARCHAR(32) NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    parent_content_id VARCHAR(64) NULL REFERENCES content_items(content_id) ON DELETE CASCADE,
    title VARCHAR(128) NOT NULL,
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('VIDEO', 'ARTICLE', 'DOCUMENT', 'QUIZ', 'ASSIGNMENT')),
    sequence_number INTEGER NOT NULL,
    estimated_duration_minutes INTEGER NOT NULL CHECK (estimated_duration_minutes > 0),
    is_required BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL
);

-- 7. Activity Events (Raw Interaction Stream)
CREATE TABLE IF NOT EXISTS activity_events (
    event_id VARCHAR(96) PRIMARY KEY,
    enrollment_id VARCHAR(64) NULL REFERENCES enrollments(enrollment_id) ON DELETE SET NULL,
    learner_id VARCHAR(32) NOT NULL REFERENCES learners(learner_id) ON DELETE RESTRICT,
    course_id VARCHAR(32) NOT NULL REFERENCES courses(course_id) ON DELETE RESTRICT,
    content_id VARCHAR(64) NULL REFERENCES content_items(content_id) ON DELETE SET NULL,
    event_type VARCHAR(32) NOT NULL CHECK (event_type IN (
        'COURSE_OPENED', 'CONTENT_VIEWED', 'VIDEO_STARTED', 'VIDEO_PROGRESS',
        'VIDEO_COMPLETED', 'DOCUMENT_DOWNLOADED', 'QUIZ_STARTED', 'QUIZ_SUBMITTED',
        'LOGIN', 'COURSE_COMPLETED'
    )),
    event_timestamp_utc TIMESTAMP NOT NULL,
    source_timezone VARCHAR(64) NOT NULL,
    event_date DATE NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    device_type VARCHAR(20) NOT NULL CHECK (device_type IN ('DESKTOP', 'MOBILE', 'TABLET')),
    sync_status VARCHAR(20) NOT NULL CHECK (sync_status IN ('REALTIME', 'OFFLINE_SYNC', 'LATE_SYNC')),
    ingestion_timestamp TIMESTAMP NOT NULL,
    idempotency_key VARCHAR(64) NOT NULL
);

-- 8. Assessments
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id VARCHAR(32) PRIMARY KEY,
    course_id VARCHAR(32) NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    title VARCHAR(128) NOT NULL,
    assessment_type VARCHAR(20) NOT NULL CHECK (assessment_type IN ('QUIZ', 'EXAM', 'PROJECT', 'PEER_REVIEW')),
    max_score NUMERIC(5, 2) NOT NULL DEFAULT 100.00,
    passing_score NUMERIC(5, 2) NOT NULL DEFAULT 70.00,
    is_required BOOLEAN NOT NULL DEFAULT 1,
    due_date DATE NULL,
    created_at TIMESTAMP NOT NULL
);

-- 9. Attempts
CREATE TABLE IF NOT EXISTS attempts (
    attempt_id VARCHAR(64) PRIMARY KEY,
    assessment_id VARCHAR(32) NOT NULL REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    enrollment_id VARCHAR(64) NOT NULL REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL CHECK (attempt_number >= 1),
    score NUMERIC(5, 2) NULL,
    submitted_at TIMESTAMP NOT NULL,
    graded_at TIMESTAMP NULL,
    attempt_status VARCHAR(20) NOT NULL CHECK (attempt_status IN ('IN_PROGRESS', 'SUBMITTED', 'GRADED', 'PASSED', 'FAILED')),
    CONSTRAINT uq_enrollment_assessment_attempt UNIQUE (enrollment_id, assessment_id, attempt_number)
);

-- 10. Completion Rules
CREATE TABLE IF NOT EXISTS completion_rules (
    completion_rule_id VARCHAR(32) PRIMARY KEY,
    course_id VARCHAR(32) NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    minimum_content_completion_percentage NUMERIC(5, 2) NOT NULL DEFAULT 80.00,
    minimum_assessment_score NUMERIC(5, 2) NOT NULL DEFAULT 70.00,
    require_all_mandatory_assessments BOOLEAN NOT NULL DEFAULT 1,
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    rule_version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT 1
);

-- 11. Course Outcomes (Snapshot History Architecture)
CREATE TABLE IF NOT EXISTS course_outcomes (
    outcome_id VARCHAR(96) PRIMARY KEY,
    enrollment_id VARCHAR(64) NOT NULL REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    outcome_version INTEGER NOT NULL DEFAULT 1,
    completion_rule_id VARCHAR(32) NOT NULL REFERENCES completion_rules(completion_rule_id) ON DELETE RESTRICT,
    completion_status VARCHAR(20) NOT NULL CHECK (completion_status IN ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'INCOMPLETE', 'FAILED')),
    content_completion_percentage NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    assessment_progress_percentage NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    final_assessment_score NUMERIC(5, 2) NULL,
    calculated_at TIMESTAMP NOT NULL,
    supersedes_outcome_id VARCHAR(96) NULL REFERENCES course_outcomes(outcome_id) ON DELETE SET NULL,
    is_current BOOLEAN NOT NULL DEFAULT 1,
    outcome_reason TEXT NOT NULL
);

-- 12. Exceptions (Detected Anomaly Store)
CREATE TABLE IF NOT EXISTS exceptions (
    exception_id VARCHAR(32) PRIMARY KEY,
    issue_type VARCHAR(64) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    entity_type VARCHAR(32) NOT NULL CHECK (entity_type IN ('ACTIVITY_EVENT', 'ENROLLMENT', 'COURSE_OUTCOME', 'LEARNER', 'ATTEMPT')),
    entity_id VARCHAR(96) NOT NULL,
    detected_at TIMESTAMP NOT NULL,
    description TEXT NOT NULL,
    evidence JSON NOT NULL,
    relevant_rule VARCHAR(128) NOT NULL,
    recommended_action TEXT NOT NULL,
    resolution_status VARCHAR(20) NOT NULL DEFAULT 'OPEN' CHECK (resolution_status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE'))
);
```

---

## 3. Database Indexes

To maintain sub-100ms API response times across millions of records, specific multi-column and foreign-key indexes are created:

```sql
-- Learners
CREATE INDEX IF NOT EXISTS ix_learners_status_region ON learners (learner_status, region);

-- Courses
CREATE INDEX IF NOT EXISTS ix_courses_category ON courses (category);
CREATE INDEX IF NOT EXISTS ix_courses_instructor ON courses (instructor_id);

-- Cohorts
CREATE INDEX IF NOT EXISTS ix_cohorts_dates ON cohorts (start_date, end_date);

-- Enrollments
CREATE INDEX IF NOT EXISTS ix_enrollments_learner ON enrollments (learner_id);
CREATE INDEX IF NOT EXISTS ix_enrollments_course ON enrollments (course_id);
CREATE INDEX IF NOT EXISTS ix_enrollments_cohort ON enrollments (cohort_id);
CREATE INDEX IF NOT EXISTS ix_enrollments_status_enrolled ON enrollments (enrollment_status, enrolled_at);

-- Content Items
CREATE INDEX IF NOT EXISTS ix_content_course_seq ON content_items (course_id, sequence_number);
CREATE INDEX IF NOT EXISTS ix_content_parent ON content_items (parent_content_id);

-- Activity Events
CREATE INDEX IF NOT EXISTS ix_events_enrollment ON activity_events (enrollment_id);
CREATE INDEX IF NOT EXISTS ix_events_learner_utc ON activity_events (learner_id, event_timestamp_utc);
CREATE INDEX IF NOT EXISTS ix_events_course_utc ON activity_events (course_id, event_timestamp_utc);
CREATE INDEX IF NOT EXISTS ix_events_content ON activity_events (content_id, event_type);
CREATE INDEX IF NOT EXISTS ix_events_idempotency ON activity_events (idempotency_key);
CREATE INDEX IF NOT EXISTS ix_events_session_near_dup ON activity_events (learner_id, course_id, content_id, event_type, session_id);
CREATE INDEX IF NOT EXISTS ix_events_utc_date ON activity_events (event_timestamp_utc);

-- Assessments & Attempts
CREATE INDEX IF NOT EXISTS ix_assessments_course ON assessments (course_id);
CREATE INDEX IF NOT EXISTS ix_attempts_enrollment ON attempts (enrollment_id);
CREATE INDEX IF NOT EXISTS ix_attempts_assessment ON attempts (assessment_id);

-- Completion Rules
CREATE INDEX IF NOT EXISTS ix_rules_course_active ON completion_rules (course_id, is_active);

-- Course Outcomes
CREATE INDEX IF NOT EXISTS ix_outcomes_enrollment_current ON course_outcomes (enrollment_id, is_current);
CREATE INDEX IF NOT EXISTS ix_outcomes_status ON course_outcomes (completion_status);
CREATE INDEX IF NOT EXISTS ix_outcomes_calculated ON course_outcomes (calculated_at);

-- Exceptions
CREATE INDEX IF NOT EXISTS ix_exceptions_severity_status ON exceptions (severity, resolution_status);
CREATE INDEX IF NOT EXISTS ix_exceptions_entity ON exceptions (entity_type, entity_id);
```
