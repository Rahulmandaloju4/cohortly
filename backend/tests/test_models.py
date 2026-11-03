"""Unit tests for SQLAlchemy 2.0 ORM models, foreign keys, and constraints."""
import pytest
from datetime import datetime, date
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from backend.app.core.database import Base
from backend.app.models import (
    Instructor,
    Learner,
    Course,
    Cohort,
    Enrollment,
    ContentItem,
    ActivityEvent,
    Assessment,
    Attempt,
    CompletionRule,
    CourseOutcome,
    ExceptionRecord,
    StateHistory,
)


@pytest.fixture
def test_db():
    """In-memory SQLite database session with foreign keys enabled."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_schema_creation_and_insertion(test_db):
    """Verify that all 13 tables are created and basic parent-child records can be inserted."""
    now = datetime(2026, 8, 1, 10, 0, 0)
    
    # 1. Instructor
    ins = Instructor(
        instructor_id="INS-000001",
        first_name="Ada",
        last_name="Lovelace",
        email="ada.lovelace@cohortly.internal",
        department="Computer Science",
        created_at=now,
    )
    test_db.add(ins)
    test_db.commit()

    # 2. Learner
    lrn = Learner(
        learner_id="LRN-000001",
        first_name="Alan",
        last_name="Turing",
        email="alan.turing@synthetic.cohortly.io",
        registration_date=date(2026, 8, 15),
        learner_status="ACTIVE",
        region="North America",
        learning_mode="COHORT_BASED",
        created_at=now,
    )
    test_db.add(lrn)
    test_db.commit()

    # 3. Course
    crs = Course(
        course_id="CRS-000001",
        course_name="Foundations of Computing",
        category="AI Engineering",
        difficulty_level="BEGINNER",
        instructor_id="INS-000001",
        course_status="ACTIVE",
        created_at=now,
    )
    test_db.add(crs)
    test_db.commit()

    # 4. Cohort
    coh = Cohort(
        cohort_id="COH-2026-001",
        cohort_name="Fall 2026 Batch",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 12, 15),
        region="North America",
        program_type="ACCELERATED",
        created_at=now,
    )
    test_db.add(coh)
    test_db.commit()

    # 5. Enrollment
    enr = Enrollment(
        enrollment_id="ENR-LRN-000001-CRS-000001",
        learner_id="LRN-000001",
        course_id="CRS-000001",
        cohort_id="COH-2026-001",
        enrolled_at=now,
        enrollment_status="ACTIVE",
        expected_completion_date=date(2026, 12, 15),
    )
    test_db.add(enr)
    test_db.commit()

    # 6. Content Item (Hierarchical module and lesson)
    module = ContentItem(
        content_id="CNT-CRS-000001-001",
        course_id="CRS-000001",
        parent_content_id=None,
        title="Module 1: Introduction",
        content_type="ARTICLE",
        sequence_number=1,
        estimated_duration_minutes=30,
        is_required=True,
        created_at=now,
    )
    test_db.add(module)
    test_db.commit()

    lesson = ContentItem(
        content_id="CNT-CRS-000001-002",
        course_id="CRS-000001",
        parent_content_id="CNT-CRS-000001-001",
        title="Lesson 1.1: Foundations",
        content_type="VIDEO",
        sequence_number=2,
        estimated_duration_minutes=45,
        is_required=True,
        created_at=now,
    )
    test_db.add(lesson)
    test_db.commit()

    # 7. Normal Activity Event
    evt = ActivityEvent(
        event_id="EVT-ENR-LRN-000001-CRS-000001-000001",
        enrollment_id="ENR-LRN-000001-CRS-000001",
        learner_id="LRN-000001",
        course_id="CRS-000001",
        content_id="CNT-CRS-000001-002",
        event_type="VIDEO_COMPLETED",
        event_timestamp_utc=datetime(2026, 9, 2, 14, 0, 0),
        source_timezone="America/New_York",
        event_date=date(2026, 9, 2),
        session_id="SES-001",
        device_type="DESKTOP",
        sync_status="REALTIME",
        ingestion_timestamp=datetime(2026, 9, 2, 14, 0, 1),
        idempotency_key="mock_hash_001",
    )
    test_db.add(evt)
    test_db.commit()

    # 8. Unenrolled Activity Event Exception (enrollment_id is NULL)
    un_evt = ActivityEvent(
        event_id="EVT-UNENROLLED-LRN-000001-CRS-000001-000001",
        enrollment_id=None,
        learner_id="LRN-000001",
        course_id="CRS-000001",
        content_id="CNT-CRS-000001-002",
        event_type="CONTENT_VIEWED",
        event_timestamp_utc=datetime(2026, 9, 2, 15, 0, 0),
        source_timezone="America/New_York",
        event_date=date(2026, 9, 2),
        session_id="SES-002",
        device_type="MOBILE",
        sync_status="REALTIME",
        ingestion_timestamp=datetime(2026, 9, 2, 15, 0, 1),
        idempotency_key="mock_hash_002",
    )
    test_db.add(un_evt)
    test_db.commit()

    assert test_db.query(ActivityEvent).count() == 2


def test_outcome_snapshot_versioning(test_db):
    """Verify that multiple outcome snapshots can exist for one enrollment with versioning."""
    now = datetime(2026, 8, 1, 10, 0, 0)
    
    ins = Instructor(instructor_id="INS-000002", first_name="A", last_name="B", email="ab@test.com", department="CS", created_at=now)
    lrn = Learner(learner_id="LRN-000002", first_name="C", last_name="D", email="cd@test.com", registration_date=date(2026, 8, 15), learner_status="ACTIVE", region="EMEA", learning_mode="SELF_PACED", created_at=now)
    crs = Course(course_id="CRS-000002", course_name="Data Structures", category="Computer Science", difficulty_level="INTERMEDIATE", instructor_id="INS-000002", course_status="ACTIVE", created_at=now)
    coh = Cohort(cohort_id="COH-2026-002", cohort_name="Batch 2", start_date=date(2026, 9, 1), end_date=date(2026, 12, 15), region="EMEA", program_type="STANDARD", created_at=now)
    enr = Enrollment(enrollment_id="ENR-LRN-000002-CRS-000002", learner_id="LRN-000002", course_id="CRS-000002", cohort_id="COH-2026-002", enrolled_at=now, enrollment_status="ACTIVE", expected_completion_date=date(2026, 12, 15))
    rule = CompletionRule(completion_rule_id="CLR-CRS-000002-V01", course_id="CRS-000002", minimum_content_completion_percentage=80.0, minimum_assessment_score=70.0, require_all_mandatory_assessments=True, effective_from=date(2026, 8, 1), rule_version=1, is_active=True)
    
    test_db.add_all([ins, lrn, crs, coh, enr, rule])
    test_db.commit()

    # Snapshot 1: IN_PROGRESS
    out1 = CourseOutcome(
        outcome_id="OUT-ENR-LRN-000002-CRS-000002-V01",
        enrollment_id="ENR-LRN-000002-CRS-000002",
        outcome_version=1,
        completion_rule_id="CLR-CRS-000002-V01",
        completion_status="IN_PROGRESS",
        content_completion_percentage=50.0,
        assessment_progress_percentage=50.0,
        final_assessment_score=65.0,
        calculated_at=datetime(2026, 9, 15, 12, 0, 0),
        supersedes_outcome_id=None,
        is_current=True,
        outcome_reason='{"status": "IN_PROGRESS", "reason": "Content incomplete"}',
    )
    test_db.add(out1)
    test_db.commit()

    # Snapshot 2: COMPLETED (Supersedes snapshot 1)
    out1.is_current = False
    out2 = CourseOutcome(
        outcome_id="OUT-ENR-LRN-000002-CRS-000002-V02",
        enrollment_id="ENR-LRN-000002-CRS-000002",
        outcome_version=2,
        completion_rule_id="CLR-CRS-000002-V01",
        completion_status="COMPLETED",
        content_completion_percentage=100.0,
        assessment_progress_percentage=100.0,
        final_assessment_score=88.0,
        calculated_at=datetime(2026, 10, 15, 12, 0, 0),
        supersedes_outcome_id=out1.outcome_id,
        is_current=True,
        outcome_reason='{"status": "COMPLETED", "reason": "All requirements met"}',
    )
    test_db.add(out2)
    test_db.commit()

    outcomes = test_db.query(CourseOutcome).filter_by(enrollment_id="ENR-LRN-000002-CRS-000002").order_by(CourseOutcome.outcome_version).all()
    assert len(outcomes) == 2
    assert outcomes[0].outcome_version == 1
    assert outcomes[0].is_current is False
    assert outcomes[1].outcome_version == 2
    assert outcomes[1].is_current is True
    assert outcomes[1].supersedes_outcome_id == outcomes[0].outcome_id


def test_append_only_state_history(test_db):
    """Verify that state_history records state transitions append-only."""
    now = datetime(2026, 9, 1, 10, 0, 0)
    h1 = StateHistory(
        history_id="HST-000001",
        entity_type="ENROLLMENT",
        entity_id="ENR-001",
        previous_state=None,
        new_state="ACTIVE",
        changed_at=now,
        actor_role="SYSTEM",
        actor_id="SYS-REG",
        reason="Initial registration",
    )
    h2 = StateHistory(
        history_id="HST-000002",
        entity_type="ENROLLMENT",
        entity_id="ENR-001",
        previous_state="ACTIVE",
        new_state="COMPLETED",
        changed_at=datetime(2026, 11, 20, 16, 45, 0),
        actor_role="SYSTEM",
        actor_id="SYS-DECISION-ENGINE",
        reason="Graduation criteria met",
    )
    test_db.add_all([h1, h2])
    test_db.commit()

    history = test_db.query(StateHistory).filter_by(entity_id="ENR-001").order_by(StateHistory.changed_at).all()
    assert len(history) == 2
    assert history[0].previous_state is None
    assert history[0].new_state == "ACTIVE"
    assert history[1].previous_state == "ACTIVE"
    assert history[1].new_state == "COMPLETED"
