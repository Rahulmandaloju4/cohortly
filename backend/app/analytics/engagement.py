"""Single source of truth for weekly engagement metrics (WALER & WAEER).
Enforces identical eligibility criteria between numerators and denominators,
strictly aligned half-open reporting windows [w_start, w_end), and mathematical
boundaries (0.0% <= WALER <= 100.0%, 0.0% <= WAEER <= 100.0%) without artificial capping.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text


def calculate_weekly_engagement(
    db: Session,
    w_start: datetime,
    w_end: datetime,
    cohort_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculates WALER and WAEER for reporting interval [w_start, w_end).
    
    WALER (Weekly Active Learner Engagement Rate):
      Numerator: Distinct active learners holding an active eligible enrollment who logged
                 at least one enrolled activity event in [w_start, w_end).
      Denominator: Distinct eligible registered active learners holding at least one
                   enrollment active during [w_start, w_end).
                   
    WAEER (Weekly Active Enrollment Engagement Rate):
      Numerator: Distinct active enrollments that had at least one activity event in [w_start, w_end).
      Denominator: Distinct eligible enrollments active during [w_start, w_end).
    """
    params = {
        "w_start": w_start.strftime("%Y-%m-%d %H:%M:%S"),
        "w_end": w_end.strftime("%Y-%m-%d %H:%M:%S"),
        "w_end_date": w_end.date().isoformat(),
    }
    cohort_filter_sql = ""
    if cohort_id:
        cohort_filter_sql = " AND en.cohort_id = :cohort_id"
        params["cohort_id"] = cohort_id

    # 1. Denominator for WALER: Distinct eligible learners
    denom_learner_query = text(f"""
        SELECT COUNT(DISTINCT l.learner_id)
        FROM learners l
        JOIN enrollments en ON l.learner_id = en.learner_id
        WHERE l.learner_status = 'ACTIVE'
          AND l.registration_date <= :w_end_date
          AND en.enrolled_at <= :w_end
          AND (en.dropped_at IS NULL OR en.dropped_at >= :w_start)
          AND (en.completed_at IS NULL OR en.completed_at >= :w_start)
          {cohort_filter_sql}
    """)
    eligible_learners = db.execute(denom_learner_query, params).scalar() or 0

    # 2. Numerator for WALER: Distinct active eligible learners
    # Strictly subsets the eligible learners holding an active enrollment in the window
    num_learner_query = text(f"""
        SELECT COUNT(DISTINCT e.learner_id)
        FROM activity_events e
        JOIN learners l ON e.learner_id = l.learner_id
        JOIN enrollments en ON e.enrollment_id = en.enrollment_id
        WHERE e.event_timestamp_utc >= :w_start
          AND e.event_timestamp_utc < :w_end
          AND e.enrollment_id IS NOT NULL
          AND l.learner_status = 'ACTIVE'
          AND l.registration_date <= :w_end_date
          AND en.enrolled_at <= :w_end
          AND (en.dropped_at IS NULL OR en.dropped_at >= :w_start)
          AND (en.completed_at IS NULL OR en.completed_at >= :w_start)
          {cohort_filter_sql}
    """)
    active_learners = db.execute(num_learner_query, params).scalar() or 0

    # 3. Denominator for WAEER: Distinct eligible enrollments
    denom_enr_query = text(f"""
        SELECT COUNT(DISTINCT en.enrollment_id)
        FROM enrollments en
        JOIN learners l ON en.learner_id = l.learner_id
        WHERE l.learner_status = 'ACTIVE'
          AND l.registration_date <= :w_end_date
          AND en.enrolled_at <= :w_end
          AND (en.dropped_at IS NULL OR en.dropped_at >= :w_start)
          AND (en.completed_at IS NULL OR en.completed_at >= :w_start)
          {cohort_filter_sql}
    """)
    eligible_enrollments = db.execute(denom_enr_query, params).scalar() or 0

    # 4. Numerator for WAEER: Distinct active eligible enrollments
    num_enr_query = text(f"""
        SELECT COUNT(DISTINCT e.enrollment_id)
        FROM activity_events e
        JOIN learners l ON e.learner_id = l.learner_id
        JOIN enrollments en ON e.enrollment_id = en.enrollment_id
        WHERE e.event_timestamp_utc >= :w_start
          AND e.event_timestamp_utc < :w_end
          AND e.enrollment_id IS NOT NULL
          AND l.learner_status = 'ACTIVE'
          AND l.registration_date <= :w_end_date
          AND en.enrolled_at <= :w_end
          AND (en.dropped_at IS NULL OR en.dropped_at >= :w_start)
          AND (en.completed_at IS NULL OR en.completed_at >= :w_start)
          {cohort_filter_sql}
    """)
    active_enrollments = db.execute(num_enr_query, params).scalar() or 0

    # 5. Compute rates with true mathematical bounds
    waler = round((active_learners / eligible_learners) * 100.0, 2) if eligible_learners > 0 else 0.0
    waeer = round((active_enrollments / eligible_enrollments) * 100.0, 2) if eligible_enrollments > 0 else 0.0

    return {
        "w_start": w_start,
        "w_end": w_end,
        "eligible_learners": eligible_learners,
        "distinct_active_learners": active_learners,
        "waler": waler,
        "eligible_enrollments": eligible_enrollments,
        "distinct_active_enrollments": active_enrollments,
        "waeer": waeer,
    }
