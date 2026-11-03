"""SQLAlchemy 2.0 ORM Declarative Models for Cohortly.
Adheres strictly to the relational schema, constraints, foreign keys, and indexes.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Boolean,
    Date,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Instructor(Base):
    __tablename__ = "instructors"

    instructor_id = Column(String(32), primary_key=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    department = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False)

    courses = relationship("Course", back_populates="instructor", cascade="all, delete-orphan")


class Learner(Base):
    __tablename__ = "learners"

    learner_id = Column(String(32), primary_key=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    registration_date = Column(Date, nullable=False)
    learner_status = Column(String(20), nullable=False)  # ACTIVE, INACTIVE, SUSPENDED
    region = Column(String(32), nullable=False)
    learning_mode = Column(String(20), nullable=False)  # SELF_PACED, COHORT_BASED, BLENDED
    created_at = Column(DateTime, nullable=False)

    enrollments = relationship("Enrollment", back_populates="learner")
    activity_events = relationship("ActivityEvent", back_populates="learner")

    __table_args__ = (
        Index("ix_learners_status_region", "learner_status", "region"),
    )


class Course(Base):
    __tablename__ = "courses"

    course_id = Column(String(32), primary_key=True)
    course_name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)
    difficulty_level = Column(String(20), nullable=False)  # BEGINNER, INTERMEDIATE, ADVANCED
    instructor_id = Column(String(32), ForeignKey("instructors.instructor_id", ondelete="RESTRICT"), nullable=False)
    course_status = Column(String(20), nullable=False)  # ACTIVE, ARCHIVED, DRAFT
    created_at = Column(DateTime, nullable=False)

    instructor = relationship("Instructor", back_populates="courses")
    enrollments = relationship("Enrollment", back_populates="course")
    content_items = relationship("ContentItem", back_populates="course", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="course", cascade="all, delete-orphan")
    completion_rules = relationship("CompletionRule", back_populates="course", cascade="all, delete-orphan")
    activity_events = relationship("ActivityEvent", back_populates="course")

    __table_args__ = (
        Index("ix_courses_category", "category"),
        Index("ix_courses_instructor", "instructor_id"),
    )


class Cohort(Base):
    __tablename__ = "cohorts"

    cohort_id = Column(String(32), primary_key=True)
    cohort_name = Column(String(128), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    region = Column(String(32), nullable=False)
    program_type = Column(String(32), nullable=False)  # ACCELERATED, STANDARD, PART_TIME
    created_at = Column(DateTime, nullable=False)

    enrollments = relationship("Enrollment", back_populates="cohort")

    __table_args__ = (
        Index("ix_cohorts_dates", "start_date", "end_date"),
    )


class Enrollment(Base):
    __tablename__ = "enrollments"

    enrollment_id = Column(String(64), primary_key=True)
    learner_id = Column(String(32), ForeignKey("learners.learner_id", ondelete="RESTRICT"), nullable=False)
    course_id = Column(String(32), ForeignKey("courses.course_id", ondelete="RESTRICT"), nullable=False)
    cohort_id = Column(String(32), ForeignKey("cohorts.cohort_id", ondelete="RESTRICT"), nullable=False)
    enrolled_at = Column(DateTime, nullable=False)
    enrollment_status = Column(String(20), nullable=False)  # ACTIVE, COMPLETED, DROPPED, PAUSED
    expected_completion_date = Column(Date, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    dropped_at = Column(DateTime, nullable=True)

    learner = relationship("Learner", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    cohort = relationship("Cohort", back_populates="enrollments")
    attempts = relationship("Attempt", back_populates="enrollment", cascade="all, delete-orphan")
    course_outcomes = relationship("CourseOutcome", back_populates="enrollment", cascade="all, delete-orphan")
    activity_events = relationship("ActivityEvent", back_populates="enrollment")

    __table_args__ = (
        UniqueConstraint("learner_id", "course_id", name="uq_learner_course"),
        Index("ix_enrollments_learner", "learner_id"),
        Index("ix_enrollments_course", "course_id"),
        Index("ix_enrollments_cohort", "cohort_id"),
        Index("ix_enrollments_status_enrolled", "enrollment_status", "enrolled_at"),
    )


class ContentItem(Base):
    __tablename__ = "content_items"

    content_id = Column(String(64), primary_key=True)
    course_id = Column(String(32), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    parent_content_id = Column(String(64), ForeignKey("content_items.content_id", ondelete="CASCADE"), nullable=True)
    title = Column(String(128), nullable=False)
    content_type = Column(String(20), nullable=False)  # VIDEO, ARTICLE, DOCUMENT, QUIZ, ASSIGNMENT
    sequence_number = Column(Integer, nullable=False)
    estimated_duration_minutes = Column(Integer, nullable=False)
    is_required = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)

    course = relationship("Course", back_populates="content_items")
    children = relationship("ContentItem", backref="parent", remote_side=[content_id])
    activity_events = relationship("ActivityEvent", back_populates="content_item")

    __table_args__ = (
        Index("ix_content_course_seq", "course_id", "sequence_number"),
        Index("ix_content_parent", "parent_content_id"),
    )


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    event_id = Column(String(96), primary_key=True)
    enrollment_id = Column(String(64), ForeignKey("enrollments.enrollment_id", ondelete="SET NULL"), nullable=True)
    learner_id = Column(String(32), ForeignKey("learners.learner_id", ondelete="RESTRICT"), nullable=False)
    course_id = Column(String(32), ForeignKey("courses.course_id", ondelete="RESTRICT"), nullable=False)
    content_id = Column(String(64), ForeignKey("content_items.content_id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(32), nullable=False)
    event_timestamp_utc = Column(DateTime, nullable=False)
    source_timezone = Column(String(64), nullable=False)
    event_date = Column(Date, nullable=False)
    session_id = Column(String(64), nullable=False)
    device_type = Column(String(20), nullable=False)  # DESKTOP, MOBILE, TABLET
    sync_status = Column(String(20), nullable=False)  # REALTIME, OFFLINE_SYNC, LATE_SYNC
    ingestion_timestamp = Column(DateTime, nullable=False)
    idempotency_key = Column(String(64), nullable=False)

    enrollment = relationship("Enrollment", back_populates="activity_events")
    learner = relationship("Learner", back_populates="activity_events")
    course = relationship("Course", back_populates="activity_events")
    content_item = relationship("ContentItem", back_populates="activity_events")

    __table_args__ = (
        Index("ix_events_enrollment", "enrollment_id"),
        Index("ix_events_learner_utc", "learner_id", "event_timestamp_utc"),
        Index("ix_events_course_utc", "course_id", "event_timestamp_utc"),
        Index("ix_events_content", "content_id", "event_type"),
        Index("ix_events_idempotency", "idempotency_key"),
        Index("ix_events_session_near_dup", "learner_id", "course_id", "content_id", "event_type", "session_id"),
        Index("ix_events_utc_date", "event_timestamp_utc"),
    )


class Assessment(Base):
    __tablename__ = "assessments"

    assessment_id = Column(String(32), primary_key=True)
    course_id = Column(String(32), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(128), nullable=False)
    assessment_type = Column(String(20), nullable=False)  # QUIZ, EXAM, PROJECT, PEER_REVIEW
    max_score = Column(Numeric(5, 2), nullable=False, default=100.00)
    passing_score = Column(Numeric(5, 2), nullable=False, default=70.00)
    is_required = Column(Boolean, nullable=False, default=True)
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False)

    course = relationship("Course", back_populates="assessments")
    attempts = relationship("Attempt", back_populates="assessment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_assessments_course", "course_id"),
    )


class Attempt(Base):
    __tablename__ = "attempts"

    attempt_id = Column(String(64), primary_key=True)
    assessment_id = Column(String(32), ForeignKey("assessments.assessment_id", ondelete="CASCADE"), nullable=False)
    enrollment_id = Column(String(64), ForeignKey("enrollments.enrollment_id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    score = Column(Numeric(5, 2), nullable=True)
    submitted_at = Column(DateTime, nullable=False)
    graded_at = Column(DateTime, nullable=True)
    attempt_status = Column(String(20), nullable=False)  # IN_PROGRESS, SUBMITTED, GRADED, PASSED, FAILED

    assessment = relationship("Assessment", back_populates="attempts")
    enrollment = relationship("Enrollment", back_populates="attempts")

    __table_args__ = (
        UniqueConstraint("enrollment_id", "assessment_id", "attempt_number", name="uq_enrollment_assessment_attempt"),
        Index("ix_attempts_enrollment", "enrollment_id"),
        Index("ix_attempts_assessment", "assessment_id"),
    )


class CompletionRule(Base):
    __tablename__ = "completion_rules"

    completion_rule_id = Column(String(32), primary_key=True)
    course_id = Column(String(32), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    minimum_content_completion_percentage = Column(Numeric(5, 2), nullable=False, default=80.00)
    minimum_assessment_score = Column(Numeric(5, 2), nullable=False, default=70.00)
    require_all_mandatory_assessments = Column(Boolean, nullable=False, default=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    rule_version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)

    course = relationship("Course", back_populates="completion_rules")
    course_outcomes = relationship("CourseOutcome", back_populates="completion_rule")

    __table_args__ = (
        Index("ix_rules_course_active", "course_id", "is_active"),
    )


class CourseOutcome(Base):
    __tablename__ = "course_outcomes"

    outcome_id = Column(String(96), primary_key=True)
    enrollment_id = Column(String(64), ForeignKey("enrollments.enrollment_id", ondelete="CASCADE"), nullable=False)
    outcome_version = Column(Integer, nullable=False, default=1)
    completion_rule_id = Column(String(32), ForeignKey("completion_rules.completion_rule_id", ondelete="RESTRICT"), nullable=False)
    completion_status = Column(String(20), nullable=False)  # NOT_STARTED, IN_PROGRESS, COMPLETED, INCOMPLETE, FAILED
    content_completion_percentage = Column(Numeric(5, 2), nullable=False, default=0.00)
    assessment_progress_percentage = Column(Numeric(5, 2), nullable=False, default=0.00)
    final_assessment_score = Column(Numeric(5, 2), nullable=True)
    calculated_at = Column(DateTime, nullable=False)
    supersedes_outcome_id = Column(String(96), ForeignKey("course_outcomes.outcome_id", ondelete="SET NULL"), nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)
    outcome_reason = Column(Text, nullable=False)

    enrollment = relationship("Enrollment", back_populates="course_outcomes")
    completion_rule = relationship("CompletionRule", back_populates="course_outcomes")

    __table_args__ = (
        Index("ix_outcomes_enrollment_current", "enrollment_id", "is_current"),
        Index("ix_outcomes_status", "completion_status"),
        Index("ix_outcomes_calculated", "calculated_at"),
    )


class ExceptionRecord(Base):
    __tablename__ = "exceptions"

    exception_id = Column(String(32), primary_key=True)
    issue_type = Column(String(64), nullable=False)
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    entity_type = Column(String(32), nullable=False)
    entity_id = Column(String(96), nullable=False)
    detected_at = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=False)
    relevant_rule = Column(String(128), nullable=False)
    recommended_action = Column(Text, nullable=False)
    resolution_status = Column(String(20), nullable=False, default="OPEN")  # OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE

    __table_args__ = (
        Index("ix_exceptions_severity_status", "severity", "resolution_status"),
        Index("ix_exceptions_entity", "entity_type", "entity_id"),
    )


class StateHistory(Base):
    __tablename__ = "state_history"

    history_id = Column(String(32), primary_key=True)
    entity_type = Column(String(32), nullable=False)  # ENROLLMENT, EXCEPTION, COURSE_OUTCOME
    entity_id = Column(String(96), nullable=False)
    previous_state = Column(String(64), nullable=True)
    new_state = Column(String(64), nullable=False)
    changed_at = Column(DateTime, nullable=False)
    actor_role = Column(String(32), nullable=False)  # SYSTEM, SUPPORT_STAFF, PLATFORM_ADMIN, etc.
    actor_id = Column(String(64), nullable=True)
    reason = Column(Text, nullable=False)

    __table_args__ = (
        Index("ix_state_history_entity", "entity_type", "entity_id"),
        Index("ix_state_history_changed", "changed_at"),
    )
