"""Explainable Course Completion Decision Engine.
Evaluates enrollment completion requirements against governing active completion rules,
generates structured non-hallucinated explanations, manages historical outcome snapshots,
and records append-only state history entries.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models import (
    Enrollment,
    Course,
    ContentItem,
    Assessment,
    Attempt,
    CompletionRule,
    CourseOutcome,
    StateHistory,
    ActivityEvent,
)
from backend.app.utils.ids import make_outcome_id, make_history_id


def evaluate_enrollment_completion(db: Session, enrollment_id: str) -> Dict[str, Any]:
    """Evaluates completion status for a given enrollment based on active business rules."""
    enrollment = db.query(Enrollment).filter_by(enrollment_id=enrollment_id).first()
    if not enrollment:
        raise ValueError(f"Enrollment {enrollment_id} not found.")

    course = db.query(Course).filter_by(course_id=enrollment.course_id).first()
    if not course:
        raise ValueError(f"Course {enrollment.course_id} not found.")

    # 1. Fetch governing active completion rule
    rule = (
        db.query(CompletionRule)
        .filter_by(course_id=enrollment.course_id, is_active=True)
        .order_by(CompletionRule.rule_version.desc())
        .first()
    )
    if not rule:
        # Fallback default rule if none explicitly created
        min_content_pct = 80.0
        min_score = 70.0
        require_all_mandatory = True
        rule_version = 1
        rule_id = f"CLR-{enrollment.course_id}-DEFAULT"
    else:
        min_content_pct = float(rule.minimum_content_completion_percentage)
        min_score = float(rule.minimum_assessment_score)
        require_all_mandatory = bool(rule.require_all_mandatory_assessments)
        rule_version = rule.rule_version
        rule_id = rule.completion_rule_id

    # 2. Content Completion Evaluation
    required_contents = (
        db.query(ContentItem)
        .filter_by(course_id=enrollment.course_id, is_required=True)
        .all()
    )
    total_required_content = len(required_contents)
    
    if total_required_content > 0:
        # Completed content items: distinct required content items with completed events
        completed_content_ids = (
            db.query(ActivityEvent.content_id)
            .filter(
                ActivityEvent.enrollment_id == enrollment_id,
                ActivityEvent.event_type.in_(["VIDEO_COMPLETED", "DOCUMENT_DOWNLOADED", "CONTENT_VIEWED"]),
                ActivityEvent.content_id.in_([c.content_id for c in required_contents]),
            )
            .distinct()
            .all()
        )
        completed_content_count = len(completed_content_ids)
        content_completion_pct = round((completed_content_count / total_required_content) * 100.0, 2)
    else:
        completed_content_count = 0
        content_completion_pct = 100.0

    content_passed = content_completion_pct >= min_content_pct

    # 3. Assessment Progress & Performance Evaluation
    required_assessments = (
        db.query(Assessment)
        .filter_by(course_id=enrollment.course_id, is_required=True)
        .all()
    )
    total_required_assessments = len(required_assessments)

    passed_mandatory_assessments = []
    failed_mandatory_assessments = []
    assessment_scores = []

    for asm in required_assessments:
        attempts = (
            db.query(Attempt)
            .filter_by(enrollment_id=enrollment_id, assessment_id=asm.assessment_id)
            .order_by(Attempt.attempt_number.desc())
            .all()
        )
        if attempts:
            best_score = max((float(att.score) for att in attempts if att.score is not None), default=0.0)
            assessment_scores.append(best_score)
            if best_score >= float(asm.passing_score):
                passed_mandatory_assessments.append(asm.assessment_id)
            else:
                failed_mandatory_assessments.append({
                    "assessment_id": asm.assessment_id,
                    "title": asm.title,
                    "passing_score": float(asm.passing_score),
                    "best_score": best_score,
                })
        else:
            failed_mandatory_assessments.append({
                "assessment_id": asm.assessment_id,
                "title": asm.title,
                "passing_score": float(asm.passing_score),
                "best_score": None,
                "reason": "Not attempted",
            })

    if total_required_assessments > 0:
        assessment_progress_pct = round(
            (len(assessment_scores) / total_required_assessments) * 100.0, 2
        )
        avg_score = round(sum(assessment_scores) / len(assessment_scores), 2) if assessment_scores else 0.0
    else:
        assessment_progress_pct = 100.0
        avg_score = 100.0

    score_passed = avg_score >= min_score
    mandatory_passed = len(failed_mandatory_assessments) == 0 if require_all_mandatory else True

    # 4. Final Decision
    all_requirements_met = content_passed and score_passed and mandatory_passed

    if all_requirements_met:
        decision = "COMPLETED"
        explanation = (
            f"All completion criteria satisfied under Rule Version {rule_version}: "
            f"Content completion {content_completion_pct}% (>= {min_content_pct}%), "
            f"Assessment score {avg_score} (>= {min_score}), and all mandatory assessments passed."
        )
    elif completed_content_count == 0 and len(assessment_scores) == 0:
        decision = "NOT_STARTED"
        explanation = "No coursework has been completed or attempted yet."
    else:
        decision = "IN_PROGRESS"
        deficiencies = []
        if not content_passed:
            deficiencies.append(f"Content completion {content_completion_pct}% < required {min_content_pct}%")
        if not score_passed:
            deficiencies.append(f"Assessment score {avg_score} < required {min_score}")
        if not mandatory_passed:
            deficiencies.append(f"{len(failed_mandatory_assessments)} mandatory assessment(s) unpassed")
        explanation = "Requirements unmet: " + "; ".join(deficiencies)

    reason_payload = {
        "decision": decision,
        "rule_version": rule_version,
        "content": {
            "completion_percentage": content_completion_pct,
            "threshold_required": min_content_pct,
            "completed_items": completed_content_count,
            "total_required_items": total_required_content,
            "passed": content_passed,
        },
        "assessments": {
            "progress_percentage": assessment_progress_pct,
            "average_score": avg_score,
            "score_threshold_required": min_score,
            "score_passed": score_passed,
            "mandatory_passed": mandatory_passed,
            "failed_details": failed_mandatory_assessments,
        },
        "explanation": explanation,
    }

    return {
        "enrollment_id": enrollment_id,
        "completion_rule_id": rule_id,
        "rule_version": rule_version,
        "decision": decision,
        "content_completion_percentage": content_completion_pct,
        "assessment_progress_percentage": assessment_progress_pct,
        "final_assessment_score": avg_score if assessment_scores else None,
        "reason_payload": reason_payload,
        "explanation": explanation,
    }


def record_outcome_snapshot(
    db: Session,
    enrollment_id: str,
    actor_role: str = "SYSTEM",
    actor_id: str = "SYS-COMPLETION-ENGINE",
    calculated_at: Optional[datetime] = None,
) -> CourseOutcome:
    """Evaluates requirements and records a new historical CourseOutcome snapshot, preserving prior versions."""
    eval_result = evaluate_enrollment_completion(db, enrollment_id)

    # 1. Fetch current active outcome if any
    current_outcome = (
        db.query(CourseOutcome)
        .filter_by(enrollment_id=enrollment_id, is_current=True)
        .first()
    )

    prev_version = current_outcome.outcome_version if current_outcome else 0
    new_version = prev_version + 1
    new_outcome_id = make_outcome_id(enrollment_id, version=new_version)
    now = calculated_at or datetime(2026, 10, 22, 0, 0, 0)

    # 2. Demote existing outcome to historical
    if current_outcome:
        current_outcome.is_current = False

    # 3. Create new snapshot
    new_outcome = CourseOutcome(
        outcome_id=new_outcome_id,
        enrollment_id=enrollment_id,
        outcome_version=new_version,
        completion_rule_id=eval_result["completion_rule_id"],
        completion_status=eval_result["decision"],
        content_completion_percentage=eval_result["content_completion_percentage"],
        assessment_progress_percentage=eval_result["assessment_progress_percentage"],
        final_assessment_score=eval_result["final_assessment_score"],
        calculated_at=now,
        supersedes_outcome_id=current_outcome.outcome_id if current_outcome else None,
        is_current=True,
        outcome_reason=json.dumps(eval_result["reason_payload"]),
    )
    db.add(new_outcome)

    # 4. Update enrollment status if decision graduated to COMPLETED
    enrollment = db.query(Enrollment).filter_by(enrollment_id=enrollment_id).first()
    if enrollment and eval_result["decision"] == "COMPLETED" and enrollment.enrollment_status != "COMPLETED":
        prev_enr_state = enrollment.enrollment_status
        enrollment.enrollment_status = "COMPLETED"
        enrollment.completed_at = now

        # Append state history
        hist_count = db.query(func.count(StateHistory.history_id)).scalar() or 0
        h_id = make_history_id(hist_count + 1)
        history_entry = StateHistory(
            history_id=h_id,
            entity_type="ENROLLMENT",
            entity_id=enrollment_id,
            previous_state=prev_enr_state,
            new_state="COMPLETED",
            changed_at=now,
            actor_role=actor_role,
            actor_id=actor_id,
            reason=eval_result["explanation"],
        )
        db.add(history_entry)

    db.commit()
    db.refresh(new_outcome)
    return new_outcome
