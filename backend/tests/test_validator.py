"""Tests for the 15-Point Cross-Entity Relational and Lifecycle Validator (CHK-01 to CHK-15).
Verifies that:
1. All 15 checks execute cleanly on the generated starter database.
2. Anomaly checks report WARNING while structural checks report PASSED.
3. Deliberate integrity violations trigger FAILED status and flag is_healthy=False.
"""

import pytest
from datetime import datetime, date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import SessionLocal, Base
from backend.app.validators.integrity_validator import run_15_point_validation
from backend.app.models import Learner, Enrollment, Course, Instructor, Cohort


def test_validator_on_starter_database():
    """Verify all 15 checks run and pass on the populated starter database."""
    db = SessionLocal()
    try:
        report = run_15_point_validation(db)
        assert report["total_checks"] == 15
        assert len(report["checks"]) == 15
        assert report["is_healthy"] is True
        assert report["failed_checks"] == 0

        check_ids = [c["check_id"] for c in report["checks"]]
        expected_ids = [f"CHK-{i:02d}" for i in range(1, 16)]
        assert check_ids == expected_ids

        # Verify specific check details
        chk_map = {c["check_id"]: c for c in report["checks"]}
        assert chk_map["CHK-01"]["status"] == "PASSED"
        assert chk_map["CHK-02"]["status"] == "PASSED"
        assert chk_map["CHK-03"]["status"] == "PASSED"
        assert chk_map["CHK-14"]["status"] == "PASSED"
        assert chk_map["CHK-15"]["status"] == "PASSED"
    finally:
        db.close()


def test_validator_detects_deliberate_fk_or_lifecycle_failure():
    """Verify that a deliberate integrity violation causes validator to report FAILED."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    now = datetime(2026, 9, 1, 10, 0, 0)
    ins = Instructor(instructor_id="INS-000001", first_name="I", last_name="A", email="i@a.com", department="CS", created_at=now)
    lrn = Learner(learner_id="LRN-000001", first_name="L", last_name="A", email="l@a.com", registration_date=date(2026, 9, 15), learner_status="ACTIVE", region="North America", learning_mode="COHORT_BASED", created_at=now)
    lrn2 = Learner(learner_id="LRN-000002", first_name="M", last_name="B", email="m@b.com", registration_date=date(2026, 8, 1), learner_status="ACTIVE", region="North America", learning_mode="COHORT_BASED", created_at=now)
    crs = Course(course_id="CRS-000001", course_name="Course 1", category="AI", difficulty_level="BEGINNER", instructor_id="INS-000001", course_status="ACTIVE", created_at=now)
    coh = Cohort(cohort_id="COH-2026-001", cohort_name="Coh 1", start_date=date(2026, 9, 1), end_date=date(2026, 12, 1), region="North America", program_type="ACCELERATED", created_at=now)
    
    # Chronological violation: Enrolled on Sept 1, but registered on Sept 15 (enrolled before registered!)
    enr_inverted = Enrollment(
        enrollment_id="ENR-001",
        learner_id="LRN-000001",
        course_id="CRS-000001",
        cohort_id="COH-2026-001",
        enrolled_at=datetime(2026, 9, 1, 10, 0, 0),
        enrollment_status="ACTIVE",
        expected_completion_date=date(2026, 12, 1)
    )
    # Lifecycle violation: status COMPLETED but completed_at is NULL
    enr_bad_lifecycle = Enrollment(
        enrollment_id="ENR-002",
        learner_id="LRN-000002",
        course_id="CRS-000001",
        cohort_id="COH-2026-001",
        enrolled_at=datetime(2026, 9, 20, 10, 0, 0),
        enrollment_status="COMPLETED",
        expected_completion_date=date(2026, 12, 1),
        completed_at=None  # Violates CHK-06
    )

    session.add_all([ins, lrn, lrn2, crs, coh, enr_inverted, enr_bad_lifecycle])
    session.commit()

    report = run_15_point_validation(session)
    assert report["is_healthy"] is False
    assert report["failed_checks"] >= 2

    chk_map = {c["check_id"]: c for c in report["checks"]}
    assert chk_map["CHK-05"]["status"] == "FAILED"  # Chronological ordering failed
    assert chk_map["CHK-06"]["status"] == "FAILED"  # Lifecycle completed_at missing failed

    session.close()
