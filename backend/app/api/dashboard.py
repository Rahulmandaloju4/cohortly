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
from backend.app.schemas.dashboard import OverviewMetrics, EngagementTrendPoint, CompletionTrendPoint, AnomalyBreakdownItem
from backend.app.models import Learner, Enrollment, Course, Cohort, ActivityEvent, ExceptionRecord, CourseOutcome
from backend.app.analytics.engagement import calculate_weekly_engagement
from backend.app.services.deduplication import analyze_deduplication
from backend.app.utils.time_utils import get_iso_week_bounds

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Reference anchor
ANCHOR_DATE = date(2026, 10, 22)

# In-memory caches for dashboard trends
_COMPLETION_TREND_CACHE = None
_ENGAGEMENT_TREND_CACHE = {}


def clear_dashboard_cache():
    """Clears cached dashboard analytics."""
    global _COMPLETION_TREND_CACHE, _ENGAGEMENT_TREND_CACHE
    _COMPLETION_TREND_CACHE = None
    _ENGAGEMENT_TREND_CACHE = {}


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

    # 1. Deduplication summary: instant indexed lookup
    raw_events = db.execute(text("SELECT COUNT(*) FROM activity_events")).scalar() or 0
    exact_dup_count = db.execute(text("SELECT COUNT(*) FROM exceptions WHERE issue_type = 'DUPLICATE_ACTIVITY_EVENT'")).scalar() or 0
    dedup_events = raw_events - exact_dup_count

    # 2. Window for WALER & WAEER: 7 days prior to reference anchor
    w_end = datetime(2026, 10, 22, 0, 0, 0)
    w_start = w_end - timedelta(days=7)

    eng_metrics = calculate_weekly_engagement(db, w_start, w_end)
    waler = eng_metrics["waler"]
    waeer = eng_metrics["waeer"]

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

    # 5. Active anomaly count & breakdown
    active_breakdown_rows = db.query(
        ExceptionRecord.issue_type,
        ExceptionRecord.severity,
        func.count(ExceptionRecord.exception_id).label("count"),
        func.min(ExceptionRecord.description).label("description")
    ).filter(
        ExceptionRecord.resolution_status.in_(["OPEN", "INVESTIGATING"])
    ).group_by(ExceptionRecord.issue_type, ExceptionRecord.severity).order_by(
        func.count(ExceptionRecord.exception_id).desc()
    ).all()

    active_anomalies = sum(r.count for r in active_breakdown_rows)
    breakdown_list = [
        AnomalyBreakdownItem(
            issue_type=r.issue_type,
            count=r.count,
            severity=r.severity,
            description=r.description
        )
        for r in active_breakdown_rows
    ]

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
        active_anomalies_breakdown=breakdown_list,
        total_activity_events=raw_events,
        deduplicated_events=dedup_events,
    )


@router.get(
    "/engagement-trend",
    response_model=List[EngagementTrendPoint],
    summary="Get multi-week engagement trends (WALER & WAEER)",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF, Roles.LEARNER))]
)
def get_engagement_trend(
    weeks: int = Query(6, ge=2, le=12, description="Number of historical weeks to report"),
    db: Session = Depends(get_db)
):
    """Calculates weekly WALER and WAEER progression backwards from the anchor date."""
    if weeks in _ENGAGEMENT_TREND_CACHE:
        return _ENGAGEMENT_TREND_CACHE[weeks]

    trends = []
    anchor = datetime(2026, 10, 22, 0, 0, 0)

    for i in range(weeks - 1, -1, -1):
        w_end = anchor - timedelta(days=i * 7)
        w_start = w_end - timedelta(days=7)

        eng = calculate_weekly_engagement(db, w_start, w_end)
        label = f"W-{w_start.strftime('%m/%d')}"

        trends.append(EngagementTrendPoint(
            period_start=w_start.strftime("%Y-%m-%d"),
            period_end=w_end.strftime("%Y-%m-%d"),
            label=label,
            distinct_active_learners=eng["distinct_active_learners"],
            eligible_learners=eng["eligible_learners"],
            waler=eng["waler"],
            distinct_active_enrollments=eng["distinct_active_enrollments"],
            eligible_enrollments=eng["eligible_enrollments"],
            waeer=eng["waeer"],
        ))

    _ENGAGEMENT_TREND_CACHE[weeks] = trends
    return trends


@router.get(
    "/completion-trend",
    response_model=List[CompletionTrendPoint],
    summary="Get cohort-by-cohort graduation & completion trends",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF, Roles.LEARNER))]
)
def get_completion_trend(db: Session = Depends(get_db)):
    """Computes graduation rate and average assessment scores per cohort."""
    global _COMPLETION_TREND_CACHE
    if _COMPLETION_TREND_CACHE is not None:
        return _COMPLETION_TREND_CACHE

    agg_query = text("""
        SELECT 
            coh.cohort_id,
            coh.cohort_name,
            COUNT(en.enrollment_id) AS total_enrollments,
            SUM(CASE WHEN en.enrollment_status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_count,
            AVG(CASE WHEN co.is_current = 1 AND co.completion_status = 'COMPLETED' THEN co.final_assessment_score ELSE NULL END) AS avg_score
        FROM cohorts coh
        LEFT JOIN enrollments en ON coh.cohort_id = en.cohort_id
        LEFT JOIN course_outcomes co ON en.enrollment_id = co.enrollment_id
        GROUP BY coh.cohort_id, coh.cohort_name, coh.start_date
        ORDER BY coh.start_date ASC
    """)
    rows = db.execute(agg_query).fetchall()
    results = []

    for r in rows:
        cohort_id = r[0]
        cohort_name = r[1]
        total = r[2] or 0
        completed = r[3] or 0
        avg_score = r[4]
        rate = round((completed / total) * 100.0, 2) if total > 0 else 0.0
        avg_score_val = round(float(avg_score), 2) if avg_score is not None else None

        results.append(CompletionTrendPoint(
            cohort_id=cohort_id,
            cohort_name=cohort_name,
            total_enrollments=total,
            completed_count=completed,
            completion_rate=rate,
            avg_score=avg_score_val,
        ))

    _COMPLETION_TREND_CACHE = results
    return results
