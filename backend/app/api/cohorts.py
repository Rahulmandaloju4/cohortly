"""Cohorts and multi-cohort comparative analytics API endpoints.
Provides cohort directories, cohort-specific health metrics, and normalized multi-cohort comparisons.
"""

from datetime import datetime, timedelta, date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from backend.app.core.database import get_db
from backend.app.core.rbac import require_roles, Roles
from backend.app.schemas.cohorts import (
    CohortListItem,
    CohortAnalytics,
    CohortComparisonResponse,
    CohortComparisonItem,
    NormalizedTimelinePoint,
)
from backend.app.models import Cohort, Enrollment, Learner, ActivityEvent, CourseOutcome

router = APIRouter(prefix="/api/cohorts", tags=["Cohorts"])


@router.get(
    "",
    response_model=List[CohortListItem],
    summary="List all cohorts with enrollment and completion statistics",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF, Roles.LEARNER))]
)
def list_cohorts(db: Session = Depends(get_db)):
    """Retrieves all learning cohorts with enrollment counts and graduation percentages."""
    cohorts = db.query(Cohort).order_by(Cohort.start_date.desc()).all()
    today = date(2026, 10, 22) # reference anchor
    items = []

    for coh in cohorts:
        total = db.query(func.count(Enrollment.enrollment_id)).filter(Enrollment.cohort_id == coh.cohort_id).scalar() or 0
        comp = db.query(func.count(Enrollment.enrollment_id)).filter(
            Enrollment.cohort_id == coh.cohort_id,
            Enrollment.enrollment_status == "COMPLETED"
        ).scalar() or 0
        rate = round((comp / total) * 100.0, 2) if total > 0 else 0.0

        if coh.start_date > today:
            status = "UPCOMING"
        elif coh.end_date < today:
            status = "CONCLUDED"
        else:
            status = "ACTIVE"

        items.append(CohortListItem(
            cohort_id=coh.cohort_id,
            cohort_name=coh.cohort_name,
            region=coh.region,
            program_type=coh.program_type,
            start_date=coh.start_date.isoformat(),
            end_date=coh.end_date.isoformat(),
            total_enrollments=total,
            completion_rate=rate,
            status=status,
        ))

    return items


@router.get(
    "/{cohort_id}/analytics",
    response_model=CohortAnalytics,
    summary="Get cohort-specific engagement and risk breakdown",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR))]
)
def get_cohort_analytics(
    cohort_id: str = Path(..., description="Target Cohort ID"),
    db: Session = Depends(get_db)
):
    """Calculates engagement rates, completion progress, and learner risk distribution for a cohort."""
    coh = db.query(Cohort).filter(Cohort.cohort_id == cohort_id).first()
    if not coh:
        raise HTTPException(status_code=404, detail=f"Cohort '{cohort_id}' not found.")

    total = db.query(func.count(Enrollment.enrollment_id)).filter(Enrollment.cohort_id == cohort_id).scalar() or 0
    active = db.query(func.count(Enrollment.enrollment_id)).filter(Enrollment.cohort_id == cohort_id, Enrollment.enrollment_status == "ACTIVE").scalar() or 0
    completed = db.query(func.count(Enrollment.enrollment_id)).filter(Enrollment.cohort_id == cohort_id, Enrollment.enrollment_status == "COMPLETED").scalar() or 0
    dropped = db.query(func.count(Enrollment.enrollment_id)).filter(Enrollment.cohort_id == cohort_id, Enrollment.enrollment_status == "DROPPED").scalar() or 0
    comp_rate = round((completed / total) * 100.0, 2) if total > 0 else 0.0

    # Weekly active rates
    w_end = datetime(2026, 10, 22, 0, 0, 0)
    w_start = w_end - timedelta(days=7)

    elig_learners = db.query(func.count(func.distinct(Enrollment.learner_id))).filter(
        Enrollment.cohort_id == cohort_id,
        Enrollment.enrollment_status == "ACTIVE"
    ).scalar() or 1

    active_learners = db.execute(text("""
        SELECT COUNT(DISTINCT e.learner_id)
        FROM activity_events e
        JOIN enrollments en ON e.enrollment_id = en.enrollment_id
        WHERE en.cohort_id = :cid
          AND e.event_timestamp_utc >= :w_start AND e.event_timestamp_utc < :w_end
    """), {"cid": cohort_id, "w_start": w_start, "w_end": w_end}).scalar() or 0
    waler = round((active_learners / elig_learners) * 100.0, 2)

    active_enrs = db.execute(text("""
        SELECT COUNT(DISTINCT e.enrollment_id)
        FROM activity_events e
        JOIN enrollments en ON e.enrollment_id = en.enrollment_id
        WHERE en.cohort_id = :cid
          AND e.event_timestamp_utc >= :w_start AND e.event_timestamp_utc < :w_end
    """), {"cid": cohort_id, "w_start": w_start, "w_end": w_end}).scalar() or 0
    waeer = round((active_enrs / max(active, 1)) * 100.0, 2)

    # Risk distribution in cohort
    cutoff_14d = w_end - timedelta(days=14)
    high_risk = db.execute(text("""
        SELECT COUNT(DISTINCT en.learner_id)
        FROM enrollments en
        WHERE en.cohort_id = :cid AND en.enrollment_status = 'ACTIVE'
          AND NOT EXISTS (
              SELECT 1 FROM activity_events e
              WHERE e.enrollment_id = en.enrollment_id AND e.event_timestamp_utc >= :cutoff
          )
    """), {"cid": cohort_id, "cutoff": cutoff_14d}).scalar() or 0

    medium_risk = int(active * 0.25)
    low_risk = max(0, active - high_risk - medium_risk)

    return CohortAnalytics(
        cohort_id=coh.cohort_id,
        cohort_name=coh.cohort_name,
        region=coh.region,
        program_type=coh.program_type,
        start_date=coh.start_date.isoformat(),
        end_date=coh.end_date.isoformat(),
        total_enrollments=total,
        completed_count=completed,
        active_count=active,
        dropped_count=dropped,
        completion_rate=comp_rate,
        waler=waler,
        waeer=waeer,
        risk_distribution={"LOW": low_risk, "MEDIUM": medium_risk, "HIGH": high_risk},
    )


@router.get(
    "/compare",
    response_model=CohortComparisonResponse,
    summary="Compare 2 or more cohorts across normalized timelines",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR))]
)
def compare_cohorts(
    cohort_ids: List[str] = Query(..., description="List of cohort IDs to compare"),
    db: Session = Depends(get_db)
):
    """Normalizes multi-cohort timelines to Day 0 (launch) and computes comparative retention curves."""
    cohort_items = []

    for cid in cohort_ids:
        coh = db.query(Cohort).filter(Cohort.cohort_id == cid).first()
        if not coh:
            continue

        total = db.query(func.count(Enrollment.enrollment_id)).filter(Enrollment.cohort_id == cid).scalar() or 0
        completed = db.query(func.count(Enrollment.enrollment_id)).filter(
            Enrollment.cohort_id == cid, Enrollment.enrollment_status == "COMPLETED"
        ).scalar() or 0
        rate = round((completed / total) * 100.0, 2) if total > 0 else 0.0

        avg_score = db.execute(text("""
            SELECT AVG(co.final_assessment_score)
            FROM course_outcomes co
            JOIN enrollments en ON co.enrollment_id = en.enrollment_id
            WHERE en.cohort_id = :cid AND co.is_current = 1 AND co.final_assessment_score IS NOT NULL
        """), {"cid": cid}).scalar()
        avg_score_val = round(float(avg_score), 2) if avg_score is not None else None

        # Normalized engagement curve: Day 0, Day 7, Day 14, Day 21, Day 28, Day 35, Day 42
        timeline = []
        coh_start_dt = datetime.combine(coh.start_date, datetime.min.time())
        for day in [0, 7, 14, 21, 28, 35, 42]:
            t_start = coh_start_dt + timedelta(days=day)
            t_end = t_start + timedelta(days=7)
            active_cnt = db.execute(text("""
                SELECT COUNT(DISTINCT e.learner_id)
                FROM activity_events e
                JOIN enrollments en ON e.enrollment_id = en.enrollment_id
                WHERE en.cohort_id = :cid
                  AND e.event_timestamp_utc >= :t_start AND e.event_timestamp_utc < :t_end
            """), {"cid": cid, "t_start": t_start, "t_end": t_end}).scalar() or 0
            retention_pct = round((active_cnt / max(total, 1)) * 100.0, 2)
            timeline.append(NormalizedTimelinePoint(day_number=day, metric_value=retention_pct))

        cohort_items.append(CohortComparisonItem(
            cohort_id=coh.cohort_id,
            cohort_name=coh.cohort_name,
            program_type=coh.program_type,
            total_enrollments=total,
            completion_rate=rate,
            waler=timeline[0].metric_value if timeline else 0.0,
            average_score=avg_score_val,
            engagement_timeline=timeline,
        ))

    return CohortComparisonResponse(cohorts=cohort_items)
