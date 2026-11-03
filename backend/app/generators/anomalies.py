"""Isolated edge-case anomaly injection and ground-truth ledger management.
CRITICAL RULE:
The ground truth file (data/ground_truth/anomalies.json) is strictly isolated.
It is NEVER queried by operational analytics, anomaly detectors, or REST API endpoints.
It is only used by independent evaluation benchmark harnesses.
"""

import json
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from backend.app.utils.ids import make_unenrolled_event_id, make_event_id, make_outcome_id
from backend.app.utils.crypto import compute_idempotency_key


def inject_anomalies(
    db_session,
    learners: List[Any],
    courses: List[Any],
    enrollments: List[Any],
    events: List[Any],
    outcomes: List[Any],
    assessments: List[Any],
    attempts: List[Any],
    rules: List[Any],
    ground_truth_path: str = "data/ground_truth/anomalies.json",
) -> List[Dict[str, Any]]:
    """Injects labelled edge cases post-baseline and writes an isolated ground-truth ledger."""
    ground_truth_records = []
    anomaly_counter = 1

    # -------------------------------------------------------------
    # 1. DUPLICATE_ACTIVITY_EVENT
    # Duplicate existing valid events (identical idempotency key, content, session, timestamp)
    # -------------------------------------------------------------
    duplicate_events = []
    # Pick first 5 valid events with an enrollment
    for evt in [e for e in events if e.enrollment_id is not None][:5]:
        dup_id = f"{evt.event_id}-DUP"
        dup_event = {
            "event_id": dup_id,
            "enrollment_id": evt.enrollment_id,
            "learner_id": evt.learner_id,
            "course_id": evt.course_id,
            "content_id": evt.content_id,
            "event_type": evt.event_type,
            "event_timestamp_utc": evt.event_timestamp_utc,
            "source_timezone": evt.source_timezone,
            "event_date": evt.event_date,
            "session_id": evt.session_id,
            "device_type": evt.device_type,
            "sync_status": "OFFLINE_SYNC",  # often caused by offline retry
            "ingestion_timestamp": evt.ingestion_timestamp + timedelta(seconds=2),
            "idempotency_key": evt.idempotency_key,  # Identical key
        }
        duplicate_events.append(dup_event)

        ground_truth_records.append({
            "anomaly_id": f"ANO-{anomaly_counter:04d}",
            "issue_type": "DUPLICATE_ACTIVITY_EVENT",
            "affected_record_id": dup_id,
            "expected_detection": "DUPLICATE_ACTIVITY_EVENT",
            "ground_truth_label": "EXACT_DUPLICATE",
            "description": f"Exact duplicate event injected with identical idempotency key '{evt.idempotency_key}'.",
            "original_record_id": evt.event_id,
        })
        anomaly_counter += 1

    # -------------------------------------------------------------
    # 2. UNENROLLED_LEARNER_ACTIVITY
    # Learner LRN-X interacts with Course CRS-Y without any enrollment
    # -------------------------------------------------------------
    unenrolled_events = []
    # Find a learner and course with NO enrollment
    enrolled_pairs = {(e.learner_id, e.course_id) for e in enrollments}
    target_learner = learners[0]
    target_course = None
    for c in courses:
        if (target_learner.learner_id, c.course_id) not in enrolled_pairs:
            target_course = c
            break

    if target_course:
        un_event_id = make_unenrolled_event_id(target_learner.learner_id, target_course.course_id, 1)
        ts_utc = datetime(2026, 9, 20, 14, 0, 0)
        idemp = compute_idempotency_key(
            target_learner.learner_id,
            target_course.course_id,
            None,
            "COURSE_OPENED",
            "SES-ANOMALY-001",
            ts_utc.isoformat() + "Z",
        )
        un_event = {
            "event_id": un_event_id,
            "enrollment_id": None,  # Nullable FK per specification
            "learner_id": target_learner.learner_id,
            "course_id": target_course.course_id,
            "content_id": None,
            "event_type": "COURSE_OPENED",
            "event_timestamp_utc": ts_utc,
            "source_timezone": "America/New_York",
            "event_date": ts_utc.date(),
            "session_id": "SES-ANOMALY-001",
            "device_type": "DESKTOP",
            "sync_status": "REALTIME",
            "ingestion_timestamp": ts_utc + timedelta(seconds=1),
            "idempotency_key": idemp,
        }
        unenrolled_events.append(un_event)

        ground_truth_records.append({
            "anomaly_id": f"ANO-{anomaly_counter:04d}",
            "issue_type": "UNENROLLED_LEARNER_ACTIVITY",
            "affected_record_id": un_event_id,
            "expected_detection": "UNENROLLED_LEARNER_ACTIVITY",
            "ground_truth_label": "UNENROLLED_ACTIVITY",
            "description": f"Learner {target_learner.learner_id} logged activity in course {target_course.course_id} without an active or historical enrollment.",
            "learner_id": target_learner.learner_id,
            "course_id": target_course.course_id,
        })
        anomaly_counter += 1

    # -------------------------------------------------------------
    # 3. PREMATURE_COMPLETION
    # Enrollment marked COMPLETED, but mandatory assessment is failed or missing
    # -------------------------------------------------------------
    premature_outcomes = []
    # Find an active enrollment that has not completed
    incomplete_enrs = [enr for enr in enrollments if enr.enrollment_status == "ACTIVE"]
    if incomplete_enrs:
        target_enr = incomplete_enrs[0]
        target_rule = next((r for r in rules if r.course_id == target_enr.course_id), rules[0])
        v1_outcome_id = make_outcome_id(target_enr.enrollment_id, 1)
        prem_outcome_id = make_outcome_id(target_enr.enrollment_id, 2)

        prem_outcome = {
            "outcome_id": prem_outcome_id,
            "enrollment_id": target_enr.enrollment_id,
            "outcome_version": 2,
            "completion_rule_id": target_rule.completion_rule_id,
            "completion_status": "COMPLETED",  # Falsely marked COMPLETED
            "content_completion_percentage": 45.0,  # Below rule threshold (e.g. 80%)
            "assessment_progress_percentage": 30.0,  # Missing mandatory assessments
            "final_assessment_score": 52.0,  # Below passing threshold
            "calculated_at": datetime(2026, 10, 10, 12, 0, 0),
            "supersedes_outcome_id": v1_outcome_id,
            "is_current": True,
            "outcome_reason": json.dumps({
                "status": "COMPLETED",
                "injected_anomaly": True,
                "note": "Corrupted outcome marking completion despite missing requirements."
            }),
        }
        premature_outcomes.append(prem_outcome)

        ground_truth_records.append({
            "anomaly_id": f"ANO-{anomaly_counter:04d}",
            "issue_type": "PREMATURE_COMPLETION",
            "affected_record_id": prem_outcome_id,
            "expected_detection": "PREMATURE_COMPLETION",
            "ground_truth_label": "RULE_VIOLATION",
            "description": f"Enrollment {target_enr.enrollment_id} marked COMPLETED despite failing content and assessment passing rules.",
            "enrollment_id": target_enr.enrollment_id,
        })
        anomaly_counter += 1

    # -------------------------------------------------------------
    # 4. TIMEZONE_DATE_MISMATCH
    # Injects an event where stored event_date differs from true derived local date
    # -------------------------------------------------------------
    timezone_mismatch_events = []
    # 23:30 UTC for Tokyo (Asia/Tokyo is UTC+9) -> Local date is next day!
    # If we corrupt the stored event_date to match UTC date or a previous date, that's an anomaly!
    if events:
        base_evt = events[-1]
        corrupted_evt_id = f"{base_evt.event_id}-TZCORRUPT"
        event_time_utc = datetime(2026, 9, 15, 23, 30, 0)  # 23:30 UTC
        # True Tokyo local date: 2026-09-16 (08:30 JST)
        # Corrupted stored date: 2026-09-15 (deliberately wrong local date)
        tz_event = {
            "event_id": corrupted_evt_id,
            "enrollment_id": base_evt.enrollment_id,
            "learner_id": base_evt.learner_id,
            "course_id": base_evt.course_id,
            "content_id": base_evt.content_id,
            "event_type": "CONTENT_VIEWED",
            "event_timestamp_utc": event_time_utc,
            "source_timezone": "Asia/Tokyo",
            "event_date": datetime(2026, 9, 15).date(),  # Deliberately corrupted! True date is 2026-09-16
            "session_id": "SES-TZ-CORRUPT",
            "device_type": "MOBILE",
            "sync_status": "REALTIME",
            "ingestion_timestamp": event_time_utc + timedelta(seconds=1),
            "idempotency_key": compute_idempotency_key(
                base_evt.learner_id, base_evt.course_id, base_evt.content_id, "CONTENT_VIEWED", "SES-TZ-CORRUPT", event_time_utc.isoformat() + "Z"
            ),
        }
        timezone_mismatch_events.append(tz_event)

        ground_truth_records.append({
            "anomaly_id": f"ANO-{anomaly_counter:04d}",
            "issue_type": "TIMEZONE_DATE_MISMATCH",
            "affected_record_id": corrupted_evt_id,
            "expected_detection": "TIMEZONE_DATE_MISMATCH",
            "ground_truth_label": "INCORRECT_LOCAL_DATE",
            "description": "Stored event_date (2026-09-15) does not match the true derived local date (2026-09-16) for Asia/Tokyo at 23:30:00 UTC.",
        })
        anomaly_counter += 1

    # -------------------------------------------------------------
    # Write Ground Truth Ledger to Isolated File
    # -------------------------------------------------------------
    os.makedirs(os.path.dirname(ground_truth_path), exist_ok=True)
    with open(ground_truth_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth_records, f, indent=2)

    return {
        "duplicate_events": duplicate_events,
        "unenrolled_events": unenrolled_events,
        "premature_outcomes": premature_outcomes,
        "timezone_mismatch_events": timezone_mismatch_events,
        "ground_truth_records": ground_truth_records,
    }
