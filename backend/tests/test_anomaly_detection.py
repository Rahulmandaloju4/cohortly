"""Unit and integration tests for the relational anomaly detection engine.
Verifies that all 4 anomaly types are accurately detected via SQL/relational rules,
properly populated into the exceptions table, and contain explainable evidence payloads.
"""

import pytest
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.models import (
    Instructor,
    Learner,
    Course,
    Cohort,
    Enrollment,
    ContentItem,
    Assessment,
    Attempt,
    CompletionRule,
    CourseOutcome,
    ActivityEvent,
    ExceptionRecord,
)
from backend.app.services.anomaly_detector import scan_and_register_anomalies
from backend.app.utils.crypto import compute_idempotency_key


@pytest.fixture
def anomaly_test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    now = datetime(2026, 9, 1, 10, 0, 0)
    ins = Instructor(instructor_id="INS-000001", first_name="Alan", last_name="Turing", email="alan@example.com", department="Computer Science", created_at=now)
    lrn1 = Learner(learner_id="LRN-000001", first_name="Ada", last_name="Lovelace", email="ada@example.com", registration_date=date(2026, 8, 1), learner_status="ACTIVE", region="North America", learning_mode="COHORT_BASED", created_at=now)
    lrn2 = Learner(learner_id="LRN-000002", first_name="Grace", last_name="Hopper", email="grace@example.com", registration_date=date(2026, 8, 1), learner_status="ACTIVE", region="Europe", learning_mode="SELF_PACED", created_at=now)
    crs = Course(course_id="CRS-000001", course_name="Foundations of AI", category="AI", difficulty_level="INTERMEDIATE", instructor_id="INS-000001", course_status="ACTIVE", created_at=now)
    coh = Cohort(cohort_id="COH-2026-001", cohort_name="Cohort Alpha", start_date=date(2026, 9, 1), end_date=date(2026, 12, 1), region="North America", program_type="ACCELERATED", created_at=now)
    
    # Enrolled learner 1
    enr1 = Enrollment(enrollment_id="ENR-000001", learner_id="LRN-000001", course_id="CRS-000001", cohort_id="COH-2026-001", enrolled_at=now, enrollment_status="ACTIVE", expected_completion_date=date(2026, 12, 1))

    # Course content & rules
    cnt1 = ContentItem(content_id="CNT-001", course_id="CRS-000001", title="Module 1", content_type="VIDEO", sequence_number=1, estimated_duration_minutes=45, is_required=True, created_at=now)
    cnt2 = ContentItem(content_id="CNT-002", course_id="CRS-000001", title="Module 2", content_type="DOCUMENT", sequence_number=2, estimated_duration_minutes=30, is_required=True, created_at=now)
    rule = CompletionRule(completion_rule_id="CLR-CRS-000001-V01", course_id="CRS-000001", minimum_content_completion_percentage=80.0, minimum_assessment_score=70.0, require_all_mandatory_assessments=False, effective_from=date(2026, 8, 1), rule_version=1, is_active=True)

    session.add_all([ins, lrn1, lrn2, crs, coh, enr1, cnt1, cnt2, rule])
    session.commit()

    yield session
    session.close()


def test_detect_duplicate_activity_event(anomaly_test_db):
    """Verify detection of duplicate events sharing the same idempotency key."""
    t0 = datetime(2026, 9, 10, 10, 0, 0)
    key = compute_idempotency_key("LRN-000001", "CRS-000001", "CNT-001", "VIDEO_COMPLETED", "SES-10", t0.isoformat() + "Z")
    
    e1 = ActivityEvent(
        event_id="EVT-001", enrollment_id="ENR-000001", learner_id="LRN-000001", course_id="CRS-000001",
        content_id="CNT-001", event_type="VIDEO_COMPLETED", event_timestamp_utc=t0,
        source_timezone="UTC", event_date=t0.date(), session_id="SES-10", device_type="DESKTOP",
        sync_status="REALTIME", ingestion_timestamp=t0, idempotency_key=key
    )
    e2 = ActivityEvent(
        event_id="EVT-002", enrollment_id="ENR-000001", learner_id="LRN-000001", course_id="CRS-000001",
        content_id="CNT-001", event_type="VIDEO_COMPLETED", event_timestamp_utc=t0 + timedelta(seconds=1),
        source_timezone="UTC", event_date=t0.date(), session_id="SES-10", device_type="DESKTOP",
        sync_status="REALTIME", ingestion_timestamp=t0 + timedelta(seconds=2), idempotency_key=key
    )
    anomaly_test_db.add_all([e1, e2])
    anomaly_test_db.commit()

    summary = scan_and_register_anomalies(anomaly_test_db)
    assert summary["by_type"].get("DUPLICATE_ACTIVITY_EVENT", 0) == 1

    exc = anomaly_test_db.query(ExceptionRecord).filter_by(issue_type="DUPLICATE_ACTIVITY_EVENT").first()
    assert exc is not None
    assert exc.entity_id == "EVT-002"
    assert exc.severity == "MEDIUM"
    assert exc.evidence["idempotency_key"] == key


def test_detect_unenrolled_learner_activity(anomaly_test_db):
    """Verify detection of events logged by learners with no valid enrollment."""
    t0 = datetime(2026, 9, 11, 14, 0, 0)
    key = compute_idempotency_key("LRN-000002", "CRS-000001", "CNT-001", "CONTENT_VIEWED", "SES-20", t0.isoformat() + "Z")
    
    # LRN-000002 is not enrolled in CRS-000001
    orphan_evt = ActivityEvent(
        event_id="EVT-UNENROLLED-LRN-000002-CRS-000001-001",
        enrollment_id=None,
        learner_id="LRN-000002",
        course_id="CRS-000001",
        content_id="CNT-001",
        event_type="CONTENT_VIEWED",
        event_timestamp_utc=t0,
        source_timezone="UTC",
        event_date=t0.date(),
        session_id="SES-20",
        device_type="DESKTOP",
        sync_status="REALTIME",
        ingestion_timestamp=t0,
        idempotency_key=key
    )
    anomaly_test_db.add(orphan_evt)
    anomaly_test_db.commit()

    summary = scan_and_register_anomalies(anomaly_test_db)
    assert summary["by_type"].get("UNENROLLED_LEARNER_ACTIVITY", 0) >= 1

    exc = anomaly_test_db.query(ExceptionRecord).filter_by(entity_id="EVT-UNENROLLED-LRN-000002-CRS-000001-001").first()
    assert exc is not None
    assert exc.issue_type == "UNENROLLED_LEARNER_ACTIVITY"
    assert exc.severity == "HIGH"


def test_detect_premature_completion(anomaly_test_db):
    """Verify detection of enrollments marked completed without satisfying requirements."""
    # Create outcome marked COMPLETED when student only completed 0% of content (requires 80%)
    now = datetime(2026, 9, 12, 12, 0, 0)
    premature_outcome = CourseOutcome(
        outcome_id="OUT-ENR-000001-V01",
        enrollment_id="ENR-000001",
        completion_rule_id="CLR-CRS-000001-V01",
        outcome_version=1,
        is_current=True,
        completion_status="COMPLETED",
        content_completion_percentage=0.0,
        assessment_progress_percentage=0.0,
        final_assessment_score=None,
        calculated_at=now,
        outcome_reason='{"decision": "COMPLETED", "explanation": "Manually overridden falsely"}'
    )
    anomaly_test_db.add(premature_outcome)
    anomaly_test_db.commit()

    summary = scan_and_register_anomalies(anomaly_test_db)
    assert summary["by_type"].get("PREMATURE_COMPLETION", 0) == 1

    exc = anomaly_test_db.query(ExceptionRecord).filter_by(issue_type="PREMATURE_COMPLETION").first()
    assert exc is not None
    assert exc.entity_id == "OUT-ENR-000001-V01"
    assert exc.severity == "CRITICAL"


def test_detect_timezone_date_mismatch(anomaly_test_db):
    """Verify detection of events where stored date differs from derived IANA date."""
    # 2026-10-15 02:00:00 UTC in America/New_York (UTC-4) is 2026-10-14 22:00:00 -> Date: 2026-10-14
    # Store wrong date: 2026-10-15
    ts_utc = datetime(2026, 10, 15, 2, 0, 0)
    key = compute_idempotency_key("LRN-000001", "CRS-000001", "CNT-001", "CONTENT_VIEWED", "SES-30", ts_utc.isoformat() + "Z")
    
    mismatch_evt = ActivityEvent(
        event_id="EVT-TZ-001",
        enrollment_id="ENR-000001",
        learner_id="LRN-000001",
        course_id="CRS-000001",
        content_id="CNT-001",
        event_type="CONTENT_VIEWED",
        event_timestamp_utc=ts_utc,
        source_timezone="America/New_York",
        event_date=date(2026, 10, 15),  # Corrupted: should be 2026-10-14
        session_id="SES-30",
        device_type="DESKTOP",
        sync_status="REALTIME",
        ingestion_timestamp=ts_utc,
        idempotency_key=key
    )
    anomaly_test_db.add(mismatch_evt)
    anomaly_test_db.commit()

    summary = scan_and_register_anomalies(anomaly_test_db)
    assert summary["by_type"].get("TIMEZONE_DATE_MISMATCH", 0) == 1

    exc = anomaly_test_db.query(ExceptionRecord).filter_by(entity_id="EVT-TZ-001").first()
    assert exc is not None
    assert exc.issue_type == "TIMEZONE_DATE_MISMATCH"
    assert exc.evidence["stored_event_date"] == "2026-10-15"
    assert exc.evidence["derived_local_date"] == "2026-10-14"
