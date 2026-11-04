"""Regression tests for WALER and WAEER engagement rates,
mathematical bounds, multi-enrollments, inactive learner exclusions,
half-open boundary conditions, and anomaly count reconciliation.
"""

import pytest
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.core.database import Base
from backend.app.models import (
    Instructor,
    Learner,
    Course,
    Cohort,
    Enrollment,
    ActivityEvent,
    ExceptionRecord,
    StateHistory,
)
from backend.app.analytics.engagement import calculate_weekly_engagement
from backend.app.main import app

client = TestClient(app)


def make_event(
    event_id: str,
    learner_id: str,
    enrollment_id: str,
    course_id: str,
    event_timestamp_utc: datetime,
    event_type: str = "LESSON_COMPLETED",
    idempotency_key: str = None,
) -> ActivityEvent:
    """Helper to instantiate fully populated, valid ActivityEvent objects for testing."""
    return ActivityEvent(
        event_id=event_id,
        learner_id=learner_id,
        enrollment_id=enrollment_id,
        course_id=course_id,
        event_type=event_type,
        event_timestamp_utc=event_timestamp_utc,
        source_timezone="UTC",
        event_date=event_timestamp_utc.date(),
        session_id=f"SES-{event_id}",
        device_type="DESKTOP",
        sync_status="REALTIME",
        ingestion_timestamp=event_timestamp_utc + timedelta(seconds=1),
        idempotency_key=idempotency_key or f"IDEMP-{event_id}",
    )


@pytest.fixture
def memory_db():
    """Isolated SQLite in-memory database for targeted engagement logic verification."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed instructor
    ins = Instructor(
        instructor_id="INS-TEST-001",
        first_name="Prof",
        last_name="Smith",
        email="smith@example.com",
        department="Computer Science",
        created_at=datetime(2026, 8, 1, 0, 0, 0),
    )
    session.add(ins)

    # Seed baseline course and cohort
    course1 = Course(
        course_id="CRS-TEST-001",
        course_name="Test AI Basics",
        category="Foundations",
        difficulty_level="BEGINNER",
        instructor_id="INS-TEST-001",
        course_status="ACTIVE",
        created_at=datetime(2026, 8, 1, 0, 0, 0),
    )
    course2 = Course(
        course_id="CRS-TEST-002",
        course_name="Test AI Advanced",
        category="Advanced",
        difficulty_level="ADVANCED",
        instructor_id="INS-TEST-001",
        course_status="ACTIVE",
        created_at=datetime(2026, 8, 1, 0, 0, 0),
    )
    cohort1 = Cohort(
        cohort_id="COH-TEST-001",
        cohort_name="Alpha Cohort",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 11, 1),
        region="North America",
        program_type="STANDARD",
        created_at=datetime(2026, 8, 1, 0, 0, 0),
    )
    cohort2 = Cohort(
        cohort_id="COH-TEST-002",
        cohort_name="Beta Cohort",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 11, 1),
        region="North America",
        program_type="STANDARD",
        created_at=datetime(2026, 8, 1, 0, 0, 0),
    )
    session.add_all([course1, course2, cohort1, cohort2])
    session.commit()

    yield session
    session.close()


def test_multi_enrollment_learner_counted_once_in_waler(memory_db):
    """A learner enrolled in two courses must count as 1 learner in WALER,
    but counts as 2 enrollments in WAEER.
    """
    w_start = datetime(2026, 10, 15, 0, 0, 0)
    w_end = datetime(2026, 10, 22, 0, 0, 0)

    # 1 Active learner
    learner = Learner(
        learner_id="LRN-MULTI-001",
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        registration_date=date(2026, 9, 1),
        learner_status="ACTIVE",
        region="North America",
        learning_mode="COHORT_BASED",
        created_at=datetime(2026, 9, 1, 0, 0, 0),
    )
    memory_db.add(learner)

    # 2 Enrollments for this same learner
    en1 = Enrollment(
        enrollment_id="ENR-MULTI-001",
        learner_id="LRN-MULTI-001",
        course_id="CRS-TEST-001",
        cohort_id="COH-TEST-001",
        enrolled_at=datetime(2026, 9, 5, 10, 0, 0),
        enrollment_status="ACTIVE",
        expected_completion_date=date(2026, 11, 1),
    )
    en2 = Enrollment(
        enrollment_id="ENR-MULTI-002",
        learner_id="LRN-MULTI-001",
        course_id="CRS-TEST-002",
        cohort_id="COH-TEST-002",
        enrolled_at=datetime(2026, 9, 6, 10, 0, 0),
        enrollment_status="ACTIVE",
        expected_completion_date=date(2026, 11, 1),
    )
    memory_db.add_all([en1, en2])

    # Activity event in Course 1 within window
    event1 = make_event(
        event_id="EVT-001",
        learner_id="LRN-MULTI-001",
        enrollment_id="ENR-MULTI-001",
        course_id="CRS-TEST-001",
        event_timestamp_utc=datetime(2026, 10, 18, 12, 0, 0),
        event_type="LESSON_COMPLETED",
    )
    # Activity event in Course 2 within window
    event2 = make_event(
        event_id="EVT-002",
        learner_id="LRN-MULTI-001",
        enrollment_id="ENR-MULTI-002",
        course_id="CRS-TEST-002",
        event_timestamp_utc=datetime(2026, 10, 19, 14, 0, 0),
        event_type="QUIZ_SUBMITTED",
    )
    memory_db.add_all([event1, event2])
    memory_db.commit()

    res = calculate_weekly_engagement(memory_db, w_start, w_end)

    # WALER: 1 distinct eligible learner, 1 active learner => 100.0%
    assert res["eligible_learners"] == 1
    assert res["distinct_active_learners"] == 1
    assert res["waler"] == 100.0

    # WAEER: 2 distinct eligible enrollments, 2 active enrollments => 100.0%
    assert res["eligible_enrollments"] == 2
    assert res["distinct_active_enrollments"] == 2
    assert res["waeer"] == 100.0

    # If event2 is deleted, learner is still active (WALER remains 100%), but only 1 enrollment active (WAEER = 50%)
    memory_db.delete(event2)
    memory_db.commit()

    res2 = calculate_weekly_engagement(memory_db, w_start, w_end)
    assert res2["eligible_learners"] == 1
    assert res2["distinct_active_learners"] == 1
    assert res2["waler"] == 100.0

    assert res2["eligible_enrollments"] == 2
    assert res2["distinct_active_enrollments"] == 1
    assert res2["waeer"] == 50.0


def test_inactive_and_dropped_learners_excluded(memory_db):
    """Inactive or suspended learners logging events must not inflate numerator or denominator."""
    w_start = datetime(2026, 10, 15, 0, 0, 0)
    w_end = datetime(2026, 10, 22, 0, 0, 0)

    # Inactive learner
    inactive_learner = Learner(
        learner_id="LRN-INACTIVE-001",
        first_name="Ghost",
        last_name="User",
        email="ghost@example.com",
        registration_date=date(2026, 9, 1),
        learner_status="SUSPENDED",
        region="Europe",
        learning_mode="COHORT_BASED",
        created_at=datetime(2026, 9, 1, 0, 0, 0),
    )
    en_inact = Enrollment(
        enrollment_id="ENR-INACT-001",
        learner_id="LRN-INACTIVE-001",
        course_id="CRS-TEST-001",
        cohort_id="COH-TEST-001",
        enrolled_at=datetime(2026, 9, 5, 10, 0, 0),
        enrollment_status="DROPPED",
        expected_completion_date=date(2026, 11, 1),
        dropped_at=datetime(2026, 10, 1, 0, 0, 0),  # Dropped before reporting window
    )
    # Event logged by suspended learner
    event_inact = make_event(
        event_id="EVT-INACT-001",
        learner_id="LRN-INACTIVE-001",
        enrollment_id="ENR-INACT-001",
        course_id="CRS-TEST-001",
        event_timestamp_utc=datetime(2026, 10, 18, 12, 0, 0),
    )
    memory_db.add_all([inactive_learner, en_inact, event_inact])
    memory_db.commit()

    res = calculate_weekly_engagement(memory_db, w_start, w_end)
    assert res["eligible_learners"] == 0
    assert res["distinct_active_learners"] == 0
    assert res["waler"] == 0.0
    assert res["eligible_enrollments"] == 0
    assert res["distinct_active_enrollments"] == 0
    assert res["waeer"] == 0.0


def test_window_half_open_boundaries(memory_db):
    """Reporting window is [w_start, w_end).
    - Event at w_start is included.
    - Event 1 second before w_start is excluded.
    - Event at w_end is excluded.
    - Event 1 second before w_end is included.
    """
    w_start = datetime(2026, 10, 15, 0, 0, 0)
    w_end = datetime(2026, 10, 22, 0, 0, 0)

    learner = Learner(
        learner_id="LRN-BOUND-001",
        first_name="Boundary",
        last_name="Tester",
        email="bound@example.com",
        registration_date=date(2026, 9, 1),
        learner_status="ACTIVE",
        region="North America",
        learning_mode="COHORT_BASED",
        created_at=datetime(2026, 9, 1, 0, 0, 0),
    )
    en = Enrollment(
        enrollment_id="ENR-BOUND-001",
        learner_id="LRN-BOUND-001",
        course_id="CRS-TEST-001",
        cohort_id="COH-TEST-001",
        enrolled_at=datetime(2026, 9, 5, 10, 0, 0),
        enrollment_status="ACTIVE",
        expected_completion_date=date(2026, 11, 1),
    )
    memory_db.add_all([learner, en])
    memory_db.commit()

    # Case 1: Event 1 second before w_start -> excluded
    evt_before = make_event(
        event_id="EVT-B-001",
        learner_id="LRN-BOUND-001",
        enrollment_id="ENR-BOUND-001",
        course_id="CRS-TEST-001",
        event_timestamp_utc=w_start - timedelta(seconds=1),
        event_type="VIDEO_WATCHED",
    )
    memory_db.add(evt_before)
    memory_db.commit()

    res = calculate_weekly_engagement(memory_db, w_start, w_end)
    assert res["eligible_learners"] == 1
    assert res["distinct_active_learners"] == 0
    assert res["waler"] == 0.0

    # Case 2: Event exactly at w_start -> included
    evt_start = make_event(
        event_id="EVT-B-002",
        learner_id="LRN-BOUND-001",
        enrollment_id="ENR-BOUND-001",
        course_id="CRS-TEST-001",
        event_timestamp_utc=w_start,
        event_type="VIDEO_WATCHED",
    )
    memory_db.add(evt_start)
    memory_db.commit()

    res = calculate_weekly_engagement(memory_db, w_start, w_end)
    assert res["distinct_active_learners"] == 1
    assert res["waler"] == 100.0

    # Remove evt_start and test w_end boundaries
    memory_db.delete(evt_start)
    memory_db.commit()

    # Case 3: Event exactly at w_end -> excluded (half-open)
    evt_end = make_event(
        event_id="EVT-B-003",
        learner_id="LRN-BOUND-001",
        enrollment_id="ENR-BOUND-001",
        course_id="CRS-TEST-001",
        event_timestamp_utc=w_end,
        event_type="VIDEO_WATCHED",
    )
    memory_db.add(evt_end)
    memory_db.commit()

    res = calculate_weekly_engagement(memory_db, w_start, w_end)
    assert res["distinct_active_learners"] == 0
    assert res["waler"] == 0.0

    # Case 4: Event 1 second before w_end -> included
    evt_just_before_end = make_event(
        event_id="EVT-B-004",
        learner_id="LRN-BOUND-001",
        enrollment_id="ENR-BOUND-001",
        course_id="CRS-TEST-001",
        event_timestamp_utc=w_end - timedelta(seconds=1),
        event_type="VIDEO_WATCHED",
    )
    memory_db.add(evt_just_before_end)
    memory_db.commit()

    res = calculate_weekly_engagement(memory_db, w_start, w_end)
    assert res["distinct_active_learners"] == 1
    assert res["waler"] == 100.0


def test_api_waler_and_waeer_strictly_bounded():
    """Verify live API returns WALER and WAEER strictly between 0% and 100% across all endpoints."""
    headers = {"X-Demo-Role": "PLATFORM_ADMIN"}

    # Overview endpoint
    overview = client.get("/api/dashboard/overview", headers=headers).json()
    assert 0.0 <= overview["waler"] <= 100.0, f"Overview WALER invalid: {overview['waler']}"
    assert 0.0 <= overview["waeer"] <= 100.0, f"Overview WAEER invalid: {overview['waeer']}"

    # Engagement trend endpoint
    trends = client.get("/api/dashboard/engagement-trend?weeks=6", headers=headers).json()
    assert len(trends) == 6
    for point in trends:
        assert 0.0 <= point["waler"] <= 100.0, f"Trend WALER invalid: {point['waler']}"
        assert 0.0 <= point["waeer"] <= 100.0, f"Trend WAEER invalid: {point['waeer']}"
        assert point["distinct_active_learners"] <= point["eligible_learners"]
        assert point["distinct_active_enrollments"] <= point["eligible_enrollments"]


def test_anomaly_counts_and_triage_reconciliation():
    """Verify that:
    1. Overview active_anomaly_count matches exceptions in OPEN or INVESTIGATING.
    2. Overview active_anomalies_breakdown totals match active_anomaly_count.
    3. Exceptions API total reflects all records in ledger (including resolved).
    4. Transitioning an exception to RESOLVED decrements active count and appends state_history.
    """
    headers = {"X-Demo-Role": "PLATFORM_ADMIN"}

    overview = client.get("/api/dashboard/overview", headers=headers).json()
    active_count = overview["active_anomaly_count"]
    breakdown = overview.get("active_anomalies_breakdown", [])

    breakdown_total = sum(item["count"] for item in breakdown)
    assert active_count == breakdown_total, f"Breakdown total {breakdown_total} != active_anomaly_count {active_count}"

    # Exceptions API
    all_exceptions = client.get("/api/exceptions?page=1&page_size=100", headers=headers).json()
    total_ledger = all_exceptions["total"]

    # Active in triage (OPEN + INVESTIGATING)
    active_in_ledger = sum(
        1 for e in all_exceptions["items"]
        if e["resolution_status"] in ("OPEN", "INVESTIGATING")
    )
    assert active_count == active_in_ledger, (
        f"Overview active count ({active_count}) does not match ledger active count ({active_in_ledger})"
    )

    # Pick first OPEN exception and test triage transition to RESOLVED
    open_items = [e for e in all_exceptions["items"] if e["resolution_status"] == "OPEN"]
    if open_items:
        target_exc_id = open_items[0]["exception_id"]

        patch_res = client.patch(
            f"/api/exceptions/{target_exc_id}/status",
            json={
                "status": "RESOLVED",
                "reason": "Verified and resolved as part of automated QA audit",
                "actor_id": "QA-ENGINEER-001",
            },
            headers=headers,
        )
        assert patch_res.status_code == 200

        # After resolving: active count should decrement by 1
        new_overview = client.get("/api/dashboard/overview", headers=headers).json()
        assert new_overview["active_anomaly_count"] == active_count - 1

        # Ledger total remains unchanged
        refreshed_exceptions = client.get("/api/exceptions?page=1&page_size=100", headers=headers).json()
        assert refreshed_exceptions["total"] == total_ledger

        # Revert back to OPEN to keep database clean
        client.patch(
            f"/api/exceptions/{target_exc_id}/status",
            json={
                "status": "OPEN",
                "reason": "Reverting QA test transition",
                "actor_id": "QA-ENGINEER-001",
            },
            headers=headers,
        )
        reverted_overview = client.get("/api/dashboard/overview", headers=headers).json()
        assert reverted_overview["active_anomaly_count"] == active_count


def test_historical_active_learner_not_excluded_by_subsequent_status_change(memory_db):
    """A learner who was actively enrolled and completed coursework in a historical week
    must NOT be excluded from that historical week's WALER calculation simply because
    their current learner_status is subsequently set to INACTIVE or SUSPENDED.
    """
    hist_w_start = datetime(2026, 9, 1, 0, 0, 0)
    hist_w_end = datetime(2026, 9, 8, 0, 0, 0)

    # Learner currently marked INACTIVE
    learner = Learner(
        learner_id="LRN-HIST-001",
        first_name="Historical",
        last_name="Active",
        email="hist@example.com",
        registration_date=date(2026, 8, 15),
        learner_status="INACTIVE",  # Current status is INACTIVE
        region="North America",
        learning_mode="COHORT_BASED",
        created_at=datetime(2026, 8, 15, 0, 0, 0),
    )
    # Enrollment was active during hist_w_start to hist_w_end
    en = Enrollment(
        enrollment_id="ENR-HIST-001",
        learner_id="LRN-HIST-001",
        course_id="CRS-TEST-001",
        cohort_id="COH-TEST-001",
        enrolled_at=datetime(2026, 8, 20, 10, 0, 0),
        enrollment_status="COMPLETED",
        expected_completion_date=date(2026, 11, 1),
        completed_at=datetime(2026, 9, 25, 0, 0, 0),  # Completed later, after historical window
    )
    # Event during the historical window
    evt = make_event(
        event_id="EVT-HIST-001",
        learner_id="LRN-HIST-001",
        enrollment_id="ENR-HIST-001",
        course_id="CRS-TEST-001",
        event_timestamp_utc=datetime(2026, 9, 4, 12, 0, 0),
    )
    memory_db.add_all([learner, en, evt])
    memory_db.commit()

    # Calculate engagement for historical week
    res = calculate_weekly_engagement(memory_db, hist_w_start, hist_w_end)
    assert res["eligible_learners"] == 1
    assert res["distinct_active_learners"] == 1
    assert res["waler"] == 100.0
