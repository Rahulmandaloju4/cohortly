"""Unit tests for deterministic ID generation formatting."""
import pytest
from backend.app.utils.ids import (
    make_instructor_id,
    make_learner_id,
    make_course_id,
    make_cohort_id,
    make_enrollment_id,
    make_content_id,
    make_event_id,
    make_unenrolled_event_id,
    make_assessment_id,
    make_attempt_id,
    make_completion_rule_id,
    make_outcome_id,
    make_exception_id,
    make_history_id,
)


def test_id_formats():
    """Verify exact string formats and zero-padded counters."""
    assert make_instructor_id(1) == "INS-000001"
    assert make_instructor_id(999999) == "INS-999999"
    
    assert make_learner_id(1) == "LRN-000001"
    assert make_learner_id(42) == "LRN-000042"
    
    assert make_course_id(1) == "CRS-000001"
    assert make_course_id(25) == "CRS-000025"
    
    assert make_cohort_id(2026, 1) == "COH-2026-001"
    
    enr_id = make_enrollment_id("LRN-000001", "CRS-000001")
    assert enr_id == "ENR-LRN-000001-CRS-000001"
    
    assert make_content_id("CRS-000001", 1) == "CNT-CRS-000001-001"
    
    # Normal event ID
    evt_id = make_event_id("ENR-LRN-000001-CRS-000001", 1)
    assert evt_id == "EVT-ENR-LRN-000001-CRS-000001-000001"
    
    # Unenrolled event ID exception
    un_evt_id = make_unenrolled_event_id("LRN-000001", "CRS-000001", 1)
    assert un_evt_id == "EVT-UNENROLLED-LRN-000001-CRS-000001-000001"
    
    assert make_assessment_id(2026, 1) == "ASM-2026-000001"
    assert make_attempt_id("ASM-2026-000001", 1) == "ATT-ASM-2026-000001-000001"
    assert make_completion_rule_id("CRS-000001", 1) == "CLR-CRS-000001-V01"
    assert make_outcome_id("ENR-LRN-000001-CRS-000001", 1) == "OUT-ENR-LRN-000001-CRS-000001-V01"
    assert make_outcome_id("ENR-LRN-000001-CRS-000001", 2) == "OUT-ENR-LRN-000001-CRS-000001-V02"
    assert make_exception_id(1) == "EXC-000001"
    assert make_history_id(1) == "HST-000001"
