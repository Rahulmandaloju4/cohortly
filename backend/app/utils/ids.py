"""Deterministic ID generation utilities for all Cohortly entities."""


def make_instructor_id(counter: int) -> str:
    """INS-000001"""
    return f"INS-{counter:06d}"


def make_learner_id(counter: int) -> str:
    """LRN-000001"""
    return f"LRN-{counter:06d}"


def make_course_id(counter: int) -> str:
    """CRS-000001"""
    return f"CRS-{counter:06d}"


def make_cohort_id(year: int, counter: int) -> str:
    """COH-2026-001"""
    return f"COH-{year}-{counter:03d}"


def make_enrollment_id(learner_id: str, course_id: str) -> str:
    """ENR-LRN-000001-CRS-000001"""
    return f"ENR-{learner_id}-{course_id}"


def make_content_id(course_id: str, seq: int) -> str:
    """CNT-CRS-000001-001"""
    return f"CNT-{course_id}-{seq:03d}"


def make_event_id(enrollment_id: str, seq: int) -> str:
    """Normal event: EVT-ENR-LRN-000001-CRS-000001-000001"""
    return f"EVT-{enrollment_id}-{seq:06d}"


def make_unenrolled_event_id(learner_id: str, course_id: str, seq: int) -> str:
    """Unenrolled activity exception: EVT-UNENROLLED-LRN-000001-CRS-000001-000001"""
    return f"EVT-UNENROLLED-{learner_id}-{course_id}-{seq:06d}"


def make_assessment_id(year: int, counter: int) -> str:
    """ASM-2026-000001"""
    return f"ASM-{year}-{counter:06d}"


def make_attempt_id(assessment_id: str, seq: int) -> str:
    """ATT-ASM-2026-000001-000001"""
    return f"ATT-{assessment_id}-{seq:06d}"


def make_completion_rule_id(course_id: str, version: int = 1) -> str:
    """CLR-CRS-000001-V01"""
    return f"CLR-{course_id}-V{version:02d}"


def make_outcome_id(enrollment_id: str, version: int = 1) -> str:
    """OUT-ENR-LRN-000001-CRS-000001-V01"""
    return f"OUT-{enrollment_id}-V{version:02d}"


def make_exception_id(counter: int) -> str:
    """EXC-000001"""
    return f"EXC-{counter:06d}"


def make_history_id(counter: int) -> str:
    """HST-000001"""
    return f"HST-{counter:06d}"
