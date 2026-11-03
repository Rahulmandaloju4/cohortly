"""Unit and integration tests for two-tier event deduplication.
Verifies exact duplicate exclusion, near-duplicate candidate retention,
and legitimate rapid repeated interaction handling.
"""

import pytest
from datetime import datetime, timedelta, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.models import ActivityEvent, Learner, Course, Enrollment, Instructor, Cohort
from backend.app.services.deduplication import analyze_deduplication
from backend.app.utils.crypto import compute_idempotency_key


@pytest.fixture
def dedup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed baseline entities
    now = datetime(2026, 9, 1, 10, 0, 0)
    ins = Instructor(instructor_id="INS-000001", first_name="I", last_name="A", email="i@a.com", department="CS", created_at=now)
    lrn = Learner(learner_id="LRN-000001", first_name="L", last_name="A", email="l@a.com", registration_date=date(2026, 8, 1), learner_status="ACTIVE", region="North America", learning_mode="COHORT_BASED", created_at=now)
    crs = Course(course_id="CRS-000001", course_name="Course 1", category="AI", difficulty_level="BEGINNER", instructor_id="INS-000001", course_status="ACTIVE", created_at=now)
    coh = Cohort(cohort_id="COH-2026-001", cohort_name="Coh 1", start_date=date(2026, 9, 1), end_date=date(2026, 12, 1), region="North America", program_type="ACCELERATED", created_at=now)
    enr = Enrollment(enrollment_id="ENR-001", learner_id="LRN-000001", course_id="CRS-000001", cohort_id="COH-2026-001", enrolled_at=now, enrollment_status="ACTIVE", expected_completion_date=date(2026, 12, 1))
    session.add_all([ins, lrn, crs, coh, enr])
    session.commit()

    yield session
    session.close()


def test_exact_duplicate_detection(dedup_db):
    """Verify exact duplicate events with identical idempotency key are counted."""
    t0 = datetime(2026, 9, 5, 14, 0, 0)
    idemp = compute_idempotency_key("LRN-000001", "CRS-000001", "CNT-001", "VIDEO_PROGRESS", "SES-1", t0.isoformat() + "Z")

    e1 = ActivityEvent(
        event_id="EVT-001", enrollment_id="ENR-001", learner_id="LRN-000001", course_id="CRS-000001",
        content_id="CNT-001", event_type="VIDEO_PROGRESS", event_timestamp_utc=t0,
        source_timezone="UTC", event_date=t0.date(), session_id="SES-1", device_type="DESKTOP",
        sync_status="REALTIME", ingestion_timestamp=t0, idempotency_key=idemp
    )
    # Exact duplicate (retry arrived 2 seconds later)
    e2 = ActivityEvent(
        event_id="EVT-002", enrollment_id="ENR-001", learner_id="LRN-000001", course_id="CRS-000001",
        content_id="CNT-001", event_type="VIDEO_PROGRESS", event_timestamp_utc=t0,
        source_timezone="UTC", event_date=t0.date(), session_id="SES-1", device_type="DESKTOP",
        sync_status="OFFLINE_SYNC", ingestion_timestamp=t0 + timedelta(seconds=2), idempotency_key=idemp
    )
    dedup_db.add_all([e1, e2])
    dedup_db.commit()

    metrics = analyze_deduplication(dedup_db)
    assert metrics["raw_event_count"] == 2
    assert metrics["exact_duplicate_count"] == 1
    assert metrics["unique_event_count"] == 1
    assert metrics["deduplicated_engagement_count"] == 1


def test_near_duplicate_candidate_retention(dedup_db):
    """Verify potential near-duplicates are flagged as candidates but NOT auto-excluded from engagement."""
    t0 = datetime(2026, 9, 6, 10, 0, 0)
    t1 = t0 + timedelta(seconds=3)  # within 5.0s tolerance

    idemp1 = compute_idempotency_key("LRN-000001", "CRS-000001", "CNT-002", "CONTENT_VIEWED", "SES-2", t0.isoformat() + "Z")
    idemp2 = compute_idempotency_key("LRN-000001", "CRS-000001", "CNT-002", "CONTENT_VIEWED", "SES-2", t1.isoformat() + "Z")

    e1 = ActivityEvent(
        event_id="EVT-003", enrollment_id="ENR-001", learner_id="LRN-000001", course_id="CRS-000001",
        content_id="CNT-002", event_type="CONTENT_VIEWED", event_timestamp_utc=t0,
        source_timezone="UTC", event_date=t0.date(), session_id="SES-2", device_type="MOBILE",
        sync_status="REALTIME", ingestion_timestamp=t0, idempotency_key=idemp1
    )
    e2 = ActivityEvent(
        event_id="EVT-004", enrollment_id="ENR-001", learner_id="LRN-000001", course_id="CRS-000001",
        content_id="CNT-002", event_type="CONTENT_VIEWED", event_timestamp_utc=t1,
        source_timezone="UTC", event_date=t1.date(), session_id="SES-2", device_type="MOBILE",
        sync_status="REALTIME", ingestion_timestamp=t1, idempotency_key=idemp2
    )
    dedup_db.add_all([e1, e2])
    dedup_db.commit()

    metrics = analyze_deduplication(dedup_db)
    # Both events are distinct idempotency keys
    assert metrics["potential_near_duplicate_count"] >= 1
    # Crucial policy check: Near-duplicates remain active in engagement count
    assert metrics["deduplicated_engagement_count"] >= 2


def test_legitimate_rapid_interactions(dedup_db):
    """Verify rapid interactions on different content items within 5s are distinct legitimate events."""
    t0 = datetime(2026, 9, 7, 11, 0, 0)
    t1 = t0 + timedelta(seconds=2)

    idemp1 = compute_idempotency_key("LRN-000001", "CRS-000001", "CNT-101", "CONTENT_VIEWED", "SES-3", t0.isoformat() + "Z")
    idemp2 = compute_idempotency_key("LRN-000001", "CRS-000001", "CNT-102", "CONTENT_VIEWED", "SES-3", t1.isoformat() + "Z")

    e1 = ActivityEvent(
        event_id="EVT-005", enrollment_id="ENR-001", learner_id="LRN-000001", course_id="CRS-000001",
        content_id="CNT-101", event_type="CONTENT_VIEWED", event_timestamp_utc=t0,
        source_timezone="UTC", event_date=t0.date(), session_id="SES-3", device_type="DESKTOP",
        sync_status="REALTIME", ingestion_timestamp=t0, idempotency_key=idemp1
    )
    e2 = ActivityEvent(
        event_id="EVT-006", enrollment_id="ENR-001", learner_id="LRN-000001", course_id="CRS-000001",
        content_id="CNT-102", event_type="CONTENT_VIEWED", event_timestamp_utc=t1,
        source_timezone="UTC", event_date=t1.date(), session_id="SES-3", device_type="DESKTOP",
        sync_status="REALTIME", ingestion_timestamp=t1, idempotency_key=idemp2
    )
    dedup_db.add_all([e1, e2])
    dedup_db.commit()

    # Different content items should NOT be considered near-duplicates
    metrics = analyze_deduplication(dedup_db)
    assert metrics["raw_event_count"] == 2
    assert metrics["potential_near_duplicate_count"] == 0
    assert metrics["exact_duplicate_count"] == 0
    assert metrics["deduplicated_engagement_count"] == 2
