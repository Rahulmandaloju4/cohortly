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

    # 1. Denominators (Combined WALER & WAEER): Distinct eligible learners and enrollments
    denom_query = text(f"""
        SELECT 
            COUNT(DISTINCT l.learner_id) AS eligible_learners,
            COUNT(DISTINCT en.enrollment_id) AS eligible_enrollments
        FROM enrollments en
        JOIN learners l ON en.learner_id = l.learner_id
        WHERE l.registration_date <= :w_end_date
          AND en.enrolled_at <= :w_end
          AND (en.dropped_at IS NULL OR en.dropped_at >= :w_start)
          AND (en.completed_at IS NULL OR en.completed_at >= :w_start)
          {cohort_filter_sql}
    """)
    denom_row = db.execute(denom_query, params).fetchone()
    eligible_learners = denom_row[0] if denom_row else 0
    eligible_enrollments = denom_row[1] if denom_row else 0

    # 2. Numerators (Combined WALER & WAEER): Active learners and active enrollments
    # High-performance EXISTS check leveraging ix_events_enr_utc index
    num_query = text(f"""
        SELECT 
            COUNT(DISTINCT en.learner_id) AS active_learners,
            COUNT(DISTINCT en.enrollment_id) AS active_enrollments
        FROM enrollments en
        JOIN learners l ON en.learner_id = l.learner_id
        WHERE l.registration_date <= :w_end_date
          AND en.enrolled_at <= :w_end
          AND (en.dropped_at IS NULL OR en.dropped_at >= :w_start)
          AND (en.completed_at IS NULL OR en.completed_at >= :w_start)
          {cohort_filter_sql}
          AND EXISTS (
              SELECT 1 FROM activity_events e
              WHERE e.enrollment_id = en.enrollment_id
                AND e.event_timestamp_utc >= :w_start
                AND e.event_timestamp_utc < :w_end
          )
    """)
    num_row = db.execute(num_query, params).fetchone()
    active_learners = num_row[0] if num_row else 0
    active_enrollments = num_row[1] if num_row else 0

    # 3. Compute rates with true mathematical bounds
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
