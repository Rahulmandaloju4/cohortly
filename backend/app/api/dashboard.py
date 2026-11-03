"""Dashboard analytics API endpoints.
Provides high-level platform KPIs, weekly WALER/WAEER engagement trends, and cohort completion trends.
"""

from datetime import datetime, timedelta, date
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from backend.app.core.database import get_db
from backend.app.core.rbac import require_roles, Roles
from backend.app.schemas.dashboard import OverviewMetrics, EngagementTrendPoint, CompletionTrendPoint
from backend.app.models import Learner, Enrollment, Course, Cohort, ActivityEvent, ExceptionRecord, CourseOutcome
from backend.app.services.deduplication import analyze_deduplication
from backend.app.utils.time_utils import get_iso_week_bounds

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Reference anchor
ANCHOR_DATE = date(2026, 10, 22)


@router.get(
    "/overview",
    response_model=OverviewMetrics,
    summary="Get overall platform KPI metrics",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF, Roles.LEARNER))]
)
def get_dashboard_overview(db: Session = Depends(get_db)):
    """Computes headline KPIs including WALER, WAEER, overall completion rate, and anomaly count."""
    total_learners = db.query(func.count(Learner.learner_id)).scalar() or 0
    active_learners = db.query(func.count(Learner.learner_id)).filter(Learner.learner_status == "ACTIVE").scalar() or 0
    total_courses = db.query(func.count(Course.course_id)).filter(Course.course_status == "ACTIVE").scalar() or 0
    active_cohorts = db.query(func.count(Cohort.cohort_id)).scalar() or 0
    total_enrollments = db.query(func.count(Enrollment.enrollment_id)).scalar() or 0

    # 1. Deduplication summary
    dedup_metrics = analyze_deduplication(db)
    raw_events = dedup_metrics["raw_event_count"]
    dedup_events = dedup_metrics["deduplicated_engagement_count"]

    # 2. Window for WALER & WAEER: 7 days prior to reference anchor
    w_end = datetime(2026, 10, 22, 0, 0, 0)
    w_start = w_end - timedelta(days=7)

    # Eligible learners: registered on or before w_end and ACTIVE
    eligible_learners_count = db.query(func.count(Learner.learner_id)).filter(
        Learner.registration_date <= w_end.date(),
        Learner.learner_status == "ACTIVE"
    ).scalar() or 1

    # Active learners in window: distinct learners with an enrolled event
    active_learners_query = text("""
        SELECT COUNT(DISTINCT e.learner_id)
        FROM activity_events e
        WHERE e.event_timestamp_utc >= :w_start
          AND e.event_timestamp_utc < :w_end
          AND e.enrollment_id IS NOT NULL
    """)
    active_learners_in_window = db.execute(
        active_learners_query, {"w_start": w_start, "w_end": w_end}
    ).scalar() or 0

    waler = round((active_learners_in_window / eligible_learners_count) * 100.0, 2)

    # Eligible enrollments: enrolled on or before w_end and not dropped before w_start
    eligible_enrs_count = db.query(func.count(Enrollment.enrollment_id)).filter(
        Enrollment.enrolled_at <= w_end,
        (Enrollment.dropped_at.is_(None) | (Enrollment.dropped_at >= w_start))
    ).scalar() or 1

    active_enrs_query = text("""
        SELECT COUNT(DISTINCT e.enrollment_id)
        FROM activity_events e
        WHERE e.event_timestamp_utc >= :w_start
          AND e.event_timestamp_utc < :w_end
          AND e.enrollment_id IS NOT NULL
    """)
    active_enrs_in_window = db.execute(
        active_enrs_query, {"w_start": w_start, "w_end": w_end}
    ).scalar() or 0

    waeer = round((active_enrs_in_window / eligible_enrs_count) * 100.0, 2)

    # 3. Overall completion rate: completed enrollments / total enrollments
    completed_enrs = db.query(func.count(Enrollment.enrollment_id)).filter(
        Enrollment.enrollment_status == "COMPLETED"
    ).scalar() or 0
    completion_rate = round((completed_enrs / total_enrollments) * 100.0, 2) if total_enrollments > 0 else 0.0

    # 4. At-risk learners: active enrollments with 0 events in last 14 days
    cutoff_14d = w_end - timedelta(days=14)
    at_risk_query = text("""
        SELECT COUNT(DISTINCT en.learner_id)
        FROM enrollments en
        WHERE en.enrollment_status = 'ACTIVE'
          AND NOT EXISTS (
              SELECT 1 FROM activity_events e
              WHERE e.enrollment_id = en.enrollment_id
                AND e.event_timestamp_utc >= :cutoff
          )
    """)
    at_risk_count = db.execute(at_risk_query, {"cutoff": cutoff_14d}).scalar() or 0

    # 5. Active anomaly count
    active_anomalies = db.query(func.count(ExceptionRecord.exception_id)).filter(
        ExceptionRecord.resolution_status.in_(["OPEN", "INVESTIGATING"])
    ).scalar() or 0

    return OverviewMetrics(
        total_learners=total_learners,
        active_learners=active_learners,
        total_courses=total_courses,
        active_cohorts=active_cohorts,
        total_enrollments=total_enrollments,
        waler=waler,
        waeer=waeer,
        overall_completion_rate=completion_rate,
        at_risk_learner_count=at_risk_count,
        active_anomaly_count=active_anomalies,
        total_activity_events=raw_events,
        deduplicated_events=dedup_events,
    )


@router.get(
    "/engagement-trend",
    response_model=List[EngagementTrendPoint],
    summary="Get multi-week engagement trends (WALER & WAEER)",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF))]
)
def get_engagement_trend(
    weeks: int = Query(6, ge=2, le=12, description="Number of historical weeks to report"),
    db: Session = Depends(get_db)
):
    """Calculates weekly WALER and WAEER progression backwards from the anchor date."""
    trends = []
    anchor = datetime(2026, 10, 22, 0, 0, 0)

    for i in range(weeks - 1, -1, -1):
        w_end = anchor - timedelta(days=i * 7)
        w_start = w_end - timedelta(days=7)

        # Eligible learners
        elig_learners = db.query(func.count(Learner.learner_id)).filter(
            Learner.registration_date <= w_end.date(),
            Learner.learner_status == "ACTIVE"
        ).scalar() or 1

        active_l_q = text("""
            SELECT COUNT(DISTINCT learner_id)
            FROM activity_events
            WHERE event_timestamp_utc >= :w_start AND event_timestamp_utc < :w_end
              AND enrollment_id IS NOT NULL
        """)
        active_learners = db.execute(active_l_q, {"w_start": w_start, "w_end": w_end}).scalar() or 0
        waler = round((active_learners / elig_learners) * 100.0, 2)

        # Eligible enrollments
        elig_enrs = db.query(func.count(Enrollment.enrollment_id)).filter(
            Enrollment.enrolled_at <= w_end,
            (Enrollment.dropped_at.is_(None) | (Enrollment.dropped_at >= w_start))
        ).scalar() or 1

        active_e_q = text("""
            SELECT COUNT(DISTINCT enrollment_id)
            FROM activity_events
            WHERE event_timestamp_utc >= :w_start AND event_timestamp_utc < :w_end
              AND enrollment_id IS NOT NULL
        """)
        active_enrs = db.execute(active_e_q, {"w_start": w_start, "w_end": w_end}).scalar() or 0
        waeer = round((active_enrs / elig_enrs) * 100.0, 2)

        label = f"W-{w_start.strftime('%m/%d')}"

        trends.append(EngagementTrendPoint(
            period_start=w_start.strftime("%Y-%m-%d"),
            period_end=w_end.strftime("%Y-%m-%d"),
            label=label,
            distinct_active_learners=active_learners,
            eligible_learners=elig_learners,
            waler=waler,
            distinct_active_enrollments=active_enrs,
            eligible_enrollments=elig_enrs,
            waeer=waeer,
        ))

    return trends


@router.get(
    "/completion-trend",
    response_model=List[CompletionTrendPoint],
    summary="Get cohort-by-cohort graduation & completion trends",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR))]
)
def get_completion_trend(db: Session = Depends(get_db)):
    """Computes graduation rate and average assessment scores per cohort."""
    cohorts = db.query(Cohort).order_by(Cohort.start_date.asc()).all()
    results = []

    for coh in cohorts:
        total = db.query(func.count(Enrollment.enrollment_id)).filter(Enrollment.cohort_id == coh.cohort_id).scalar() or 0
        completed = db.query(func.count(Enrollment.enrollment_id)).filter(
            Enrollment.cohort_id == coh.cohort_id,
            Enrollment.enrollment_status == "COMPLETED"
        ).scalar() or 0

        rate = round((completed / total) * 100.0, 2) if total > 0 else 0.0

        # Average final assessment score for completed learners in this cohort
        avg_score_q = text("""
            SELECT AVG(co.final_assessment_score)
            FROM course_outcomes co
            JOIN enrollments en ON co.enrollment_id = en.enrollment_id
            WHERE en.cohort_id = :coh_id
              AND co.is_current = 1
              AND co.completion_status = 'COMPLETED'
              AND co.final_assessment_score IS NOT NULL
        """)
        avg_score = db.execute(avg_score_q, {"coh_id": coh.cohort_id}).scalar()
        avg_score_val = round(float(avg_score), 2) if avg_score is not None else None

        results.append(CompletionTrendPoint(
            cohort_id=coh.cohort_id,
            cohort_name=coh.cohort_name,
            total_enrollments=total,
            completed_count=completed,
            completion_rate=rate,
            avg_score=avg_score_val,
        ))

    return results
