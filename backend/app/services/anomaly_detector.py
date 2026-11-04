"""Operational Relational Anomaly Detection Engine.
STRICT ISOLATION RULE:
This engine queries operational database records ONLY.
It NEVER references, imports, or joins the ground truth ledger.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.models import ExceptionRecord, CourseOutcome, Enrollment, CompletionRule, ActivityEvent
from backend.app.utils.ids import make_exception_id
from backend.app.utils.time_utils import is_timezone_date_consistent
from backend.app.services.completion_engine import evaluate_enrollment_completion


def scan_and_register_anomalies(db: Session, detection_time: Optional[datetime] = None) -> Dict[str, Any]:
    """Runs pure relational rules to detect data anomalies and registers them into the exceptions table."""
    if detection_time is None:
        # Default to deterministic anchor detection timestamp: 2026-10-22 01:00:00 UTC
        detection_time = datetime(2026, 10, 22, 1, 0, 0)
    now = detection_time
    detected_exceptions = []
    
    # Existing exception counter to ensure deterministic incremental IDs
    existing_count = db.execute(text("SELECT COUNT(*) FROM exceptions")).scalar() or 0
    exc_counter = existing_count + 1

    # -------------------------------------------------------------
    # 1. ANOMALY 1: DUPLICATE_ACTIVITY_EVENT
    # Exact duplicate events with identical idempotency key
    # -------------------------------------------------------------
    duplicate_query = text("""
        SELECT e.event_id, e.idempotency_key, e.learner_id, e.course_id, e.event_type, e.event_timestamp_utc
        FROM activity_events e
        WHERE e.idempotency_key IN (
            SELECT idempotency_key
            FROM activity_events
            GROUP BY idempotency_key
            HAVING COUNT(*) > 1
        )
        ORDER BY e.idempotency_key, e.ingestion_timestamp ASC, e.rowid ASC
    """)
    dup_rows = db.execute(duplicate_query).fetchall()
    
    seen_keys = set()
    for row in dup_rows:
        evt_id, idemp, lid, cid, etype, ts = row
        if idemp in seen_keys:
            # Subsequent duplicate row
            exc_id = make_exception_id(exc_counter)
            exc_counter += 1
            exc = ExceptionRecord(
                exception_id=exc_id,
                issue_type="DUPLICATE_ACTIVITY_EVENT",
                severity="MEDIUM",
                entity_type="ACTIVITY_EVENT",
                entity_id=evt_id,
                detected_at=now,
                description=f"Duplicate event detected sharing idempotency key '{idemp}'.",
                evidence={
                    "event_id": evt_id,
                    "idempotency_key": idemp,
                    "learner_id": lid,
                    "course_id": cid,
                    "event_type": etype,
                    "event_timestamp_utc": str(ts),
                },
                relevant_rule="RULE-EVENT-001: Exact Deduplication Strategy",
                recommended_action="Exclude redundant duplicate event from engagement metrics; preserve earliest canonical row.",
                resolution_status="OPEN",
            )
            detected_exceptions.append(exc)
        else:
            seen_keys.add(idemp)

    # -------------------------------------------------------------
    # 2. ANOMALY 2: UNENROLLED_LEARNER_ACTIVITY
    # Learner logged activity without a valid matching enrollment
    # -------------------------------------------------------------
    unenrolled_query = text("""
        SELECT e.event_id, e.learner_id, e.course_id, e.event_type, e.event_timestamp_utc
        FROM activity_events e
        WHERE e.enrollment_id IS NULL
           OR NOT EXISTS (
               SELECT 1 FROM enrollments en
               WHERE en.learner_id = e.learner_id AND en.course_id = e.course_id
           )
    """)
    unenrolled_rows = db.execute(unenrolled_query).fetchall()
    for row in unenrolled_rows:
        evt_id, lid, cid, etype, ts = row
        exc_id = make_exception_id(exc_counter)
        exc_counter += 1
        exc = ExceptionRecord(
            exception_id=exc_id,
            issue_type="UNENROLLED_LEARNER_ACTIVITY",
            severity="HIGH",
            entity_type="ACTIVITY_EVENT",
            entity_id=evt_id,
            detected_at=now,
            description=f"Learner {lid} logged {etype} in course {cid} without an active or historical enrollment.",
            evidence={
                "event_id": evt_id,
                "learner_id": lid,
                "course_id": cid,
                "event_type": etype,
                "event_timestamp_utc": str(ts),
                "enrollment_found": False,
            },
            relevant_rule="RULE-INTEG-001: Event-Enrollment Match",
            recommended_action="Investigate auth telemetry; enroll learner into target course or void invalid event.",
            resolution_status="OPEN",
        )
        detected_exceptions.append(exc)

    # -------------------------------------------------------------
    # 3. ANOMALY 3: PREMATURE_COMPLETION
    # Enrollment outcome marked COMPLETED despite failing business rules
    # -------------------------------------------------------------
    premature_query = text("""
        SELECT co.outcome_id, co.enrollment_id
        FROM course_outcomes co
        JOIN completion_rules cr ON co.completion_rule_id = cr.completion_rule_id
        WHERE co.completion_status = 'COMPLETED'
          AND co.is_current = 1
          AND (
              co.content_completion_percentage < cr.minimum_content_completion_percentage
              OR (cr.minimum_assessment_score IS NOT NULL AND co.final_assessment_score < cr.minimum_assessment_score)
          )
    """)
    premature_rows = db.execute(premature_query).fetchall()
    for row in premature_rows:
        outcome_id, enr_id = row[0], row[1]
        eval_result = evaluate_enrollment_completion(db, enr_id)
        if eval_result["decision"] != "COMPLETED":
            exc_id = make_exception_id(exc_counter)
            exc_counter += 1
            exc = ExceptionRecord(
                exception_id=exc_id,
                issue_type="PREMATURE_COMPLETION",
                severity="CRITICAL",
                entity_type="COURSE_OUTCOME",
                entity_id=outcome_id,
                detected_at=now,
                description=f"Enrollment {enr_id} marked COMPLETED despite failing completion requirements.",
                evidence={
                    "outcome_id": outcome_id,
                    "enrollment_id": enr_id,
                    "outcome_status": "COMPLETED",
                    "rule_evaluation": eval_result["reason_payload"],
                },
                relevant_rule="RULE-COMPL-001: Completion Eligibility Verification",
                recommended_action="Revoke completion status; recalculate outcome snapshot to IN_PROGRESS; notify student.",
                resolution_status="OPEN",
            )
            detected_exceptions.append(exc)

    # -------------------------------------------------------------
    # 4. ANOMALY 4: TIMEZONE_DATE_MISMATCH
    # Stored event_date differs from derived local date for source_timezone
    # -------------------------------------------------------------
    from backend.app.utils.time_utils import derive_local_date_from_utc
    tz_query = text("""
        SELECT event_id, event_timestamp_utc, source_timezone, event_date
        FROM activity_events
        WHERE event_date != date(event_timestamp_utc)
           OR strftime('%H', event_timestamp_utc) IN ('00','01','02','03','04','20','21','22','23')
    """)
    tz_rows = db.execute(tz_query).fetchall()

    for evt_id, ts_utc, tz_name, stored_date in tz_rows:
        if isinstance(ts_utc, str):
            ts_val = datetime.fromisoformat(ts_utc)
        else:
            ts_val = ts_utc
        if isinstance(stored_date, str):
            date_val = datetime.strptime(stored_date, "%Y-%m-%d").date()
        else:
            date_val = stored_date

        if not is_timezone_date_consistent(ts_val, tz_name, date_val):
            exc_id = make_exception_id(exc_counter)
            exc_counter += 1
            true_date = derive_local_date_from_utc(ts_val, tz_name)
            exc = ExceptionRecord(
                exception_id=exc_id,
                issue_type="TIMEZONE_DATE_MISMATCH",
                severity="LOW",
                entity_type="ACTIVITY_EVENT",
                entity_id=evt_id,
                detected_at=now,
                description=f"Stored local date ({date_val}) does not match derived date ({true_date}) for {tz_name} at {ts_val} UTC.",
                evidence={
                    "event_id": evt_id,
                    "event_timestamp_utc": str(ts_val),
                    "source_timezone": tz_name,
                    "stored_event_date": str(date_val),
                    "derived_local_date": str(true_date),
                },
                relevant_rule="RULE-ANOMALY-004: Timezone Date Conversion Consistency",
                recommended_action="Re-derive local date from UTC timestamp and IANA timezone; audit client telemetry clock.",
                resolution_status="OPEN",
            )
            detected_exceptions.append(exc)


    # -------------------------------------------------------------
    # 5. Clear and insert detected exceptions
    # -------------------------------------------------------------
    db.execute(text("DELETE FROM exceptions"))
    db.add_all(detected_exceptions)
    db.commit()

    summary = {
        "total_anomalies_detected": len(detected_exceptions),
        "by_type": {},
        "by_severity": {},
    }
    for exc in detected_exceptions:
        summary["by_type"][exc.issue_type] = summary["by_type"].get(exc.issue_type, 0) + 1
        summary["by_severity"][exc.severity] = summary["by_severity"].get(exc.severity, 0) + 1

    return summary
