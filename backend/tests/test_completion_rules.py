"""Unit tests for completion rule evaluation, outcome snapshotting, and explainable reasons."""
import pytest
import json
from datetime import datetime, date
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
    StateHistory,
)
from backend.app.services.completion_engine import evaluate_enrollment_completion, record_outcome_snapshot


@pytest.fixture
def completion_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    now = datetime(2026, 9, 1, 10, 0, 0)
    ins = Instructor(instructor_id="INS-000001", first_name="A", last_name="B", email="a@b.com", department="AI", created_at=now)
    lrn = Learner(learner_id="LRN-000001", first_name="C", last_name="D", email="c@d.com", registration_date=date(2026, 8, 1), learner_status="ACTIVE", region="North America", learning_mode="COHORT_BASED", created_at=now)
    crs = Course(course_id="CRS-000001", course_name="Machine Learning", category="AI", difficulty_level="INTERMEDIATE", instructor_id="INS-000001", course_status="ACTIVE", created_at=now)
    coh = Cohort(cohort_id="COH-2026-001", cohort_name="Fall Batch", start_date=date(2026, 9, 1), end_date=date(2026, 12, 1), region="North America", program_type="ACCELERATED", created_at=now)
    enr = Enrollment(enrollment_id="ENR-001", learner_id="LRN-000001", course_id="CRS-000001", cohort_id="COH-2026-001", enrolled_at=now, enrollment_status="ACTIVE", expected_completion_date=date(2026, 12, 1))
    
    # 2 required content items
    c1 = ContentItem(content_id="CNT-001", course_id="CRS-000001", title="Intro", content_type="VIDEO", sequence_number=1, estimated_duration_minutes=30, is_required=True, created_at=now)
    c2 = ContentItem(content_id="CNT-002", course_id="CRS-000001", title="Practice", content_type="DOCUMENT", sequence_number=2, estimated_duration_minutes=30, is_required=True, created_at=now)
    
    # 1 mandatory assessment
    asm = Assessment(assessment_id="ASM-001", course_id="CRS-000001", title="Final Exam", assessment_type="EXAM", max_score=100.0, passing_score=70.0, is_required=True, created_at=now)
    
    # Completion rule: min 80% content, min 70% score, require all mandatory
    rule = CompletionRule(completion_rule_id="CLR-CRS-000001-V01", course_id="CRS-000001", minimum_content_completion_percentage=80.0, minimum_assessment_score=70.0, require_all_mandatory_assessments=True, effective_from=date(2026, 8, 1), rule_version=1, is_active=True)

    session.add_all([ins, lrn, crs, coh, enr, c1, c2, asm, rule])
    session.commit()

    yield session
    session.close()


def test_completion_failure_when_incomplete(completion_db):
    """Verify evaluation returns IN_PROGRESS when requirements are partially completed."""
    # Only 1 content item completed (50% < 80% required)
    evt = ActivityEvent(
        event_id="EVT-001", enrollment_id="ENR-001", learner_id="LRN-000001", course_id="CRS-000001",
        content_id="CNT-001", event_type="VIDEO_COMPLETED", event_timestamp_utc=datetime(2026, 9, 5, 12, 0, 0),
        source_timezone="UTC", event_date=date(2026, 9, 5), session_id="S1", device_type="DESKTOP",
        sync_status="REALTIME", ingestion_timestamp=datetime(2026, 9, 5, 12, 0, 1), idempotency_key="h1"
    )
    completion_db.add(evt)
    completion_db.commit()

    res = evaluate_enrollment_completion(completion_db, "ENR-001")
    assert res["decision"] == "IN_PROGRESS"
    assert res["content_completion_percentage"] == 50.0
    assert "Content completion 50.0% < required 80.0%" in res["explanation"]


def test_completion_success_and_snapshot_versioning(completion_db):
    """Verify successful graduation, snapshot creation, and state history append."""
    # Complete 1st content item
    evt1 = ActivityEvent(
        event_id="EVT-001", enrollment_id="ENR-001", learner_id="LRN-000001", course_id="CRS-000001",
        content_id="CNT-001", event_type="VIDEO_COMPLETED", event_timestamp_utc=datetime(2026, 9, 5, 12, 0, 0),
        source_timezone="UTC", event_date=date(2026, 9, 5), session_id="S1", device_type="DESKTOP",
        sync_status="REALTIME", ingestion_timestamp=datetime(2026, 9, 5, 12, 0, 1), idempotency_key="h1"
    )
    # Complete 2nd content item (100% >= 80%)
    evt2 = ActivityEvent(
        event_id="EVT-002", enrollment_id="ENR-001", learner_id="LRN-000001", course_id="CRS-000001",
        content_id="CNT-002", event_type="DOCUMENT_DOWNLOADED", event_timestamp_utc=datetime(2026, 9, 6, 12, 0, 0),
        source_timezone="UTC", event_date=date(2026, 9, 6), session_id="S2", device_type="DESKTOP",
        sync_status="REALTIME", ingestion_timestamp=datetime(2026, 9, 6, 12, 0, 1), idempotency_key="h2"
    )
    # Pass assessment with score 85.0
    att = Attempt(
        attempt_id="ATT-001", assessment_id="ASM-001", enrollment_id="ENR-001",
        attempt_number=1, score=85.0, submitted_at=datetime(2026, 9, 7, 12, 0, 0),
        graded_at=datetime(2026, 9, 7, 12, 0, 5), attempt_status="PASSED"
    )
    completion_db.add_all([evt1, evt2, att])
    completion_db.commit()

    # Record snapshot
    snapshot1 = record_outcome_snapshot(completion_db, "ENR-001")
    assert snapshot1.completion_status == "COMPLETED"
    assert snapshot1.outcome_version == 1
    assert snapshot1.is_current is True

    enr = completion_db.query(Enrollment).filter_by(enrollment_id="ENR-001").first()
    assert enr.enrollment_status == "COMPLETED"

    # Verify state history log was appended
    hist = completion_db.query(StateHistory).filter_by(entity_id="ENR-001", new_state="COMPLETED").first()
    assert hist is not None
    assert hist.previous_state == "ACTIVE"

    # Recalculate (e.g. audit recalculation) -> should create snapshot version 2
    snapshot2 = record_outcome_snapshot(completion_db, "ENR-001")
    assert snapshot2.outcome_version == 2
    assert snapshot2.is_current is True
    assert snapshot2.supersedes_outcome_id == snapshot1.outcome_id

    # Verify snapshot 1 was preserved but marked not current
    completion_db.refresh(snapshot1)
    assert snapshot1.is_current is False
    assert snapshot1.outcome_version == 1
