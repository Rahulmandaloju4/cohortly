"""Learners API endpoints.
Provides directory search, detailed learner profile with explainable outcome checklists,
and granular activity audit timelines.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import text, func, or_

from backend.app.core.database import get_db
from backend.app.core.rbac import require_roles, Roles, get_current_role
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.learners import LearnerListItem, LearnerDetail, LearnerActivityItem, EnrollmentOverview
from backend.app.models import Learner, Enrollment, Course, Cohort, ActivityEvent, CourseOutcome, Attempt

router = APIRouter(prefix="/api/learners", tags=["Learners"])


@router.get(
    "",
    response_model=PaginatedResponse[LearnerListItem],
    summary="List and search learners with filtering",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF))]
)
def list_learners(
    search: Optional[str] = Query(None, description="Search by learner name, email, or ID"),
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, INACTIVE, SUSPENDED"),
    region: Optional[str] = Query(None, description="Filter by geographic region"),
    cohort_id: Optional[str] = Query(None, description="Filter by enrolled cohort"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Returns paginated list of learners with computed enrollment counts and risk levels."""
    query = db.query(Learner)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Learner.first_name.ilike(search_pattern),
                Learner.last_name.ilike(search_pattern),
                Learner.email.ilike(search_pattern),
                Learner.learner_id.ilike(search_pattern),
            )
        )
    if status:
        query = query.filter(Learner.learner_status == status.upper())
    if region:
        query = query.filter(Learner.region == region)
    if cohort_id:
        query = query.join(Enrollment, Learner.learner_id == Enrollment.learner_id).filter(Enrollment.cohort_id == cohort_id)

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    learners = query.order_by(Learner.registration_date.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    # Reference anchor for inactivity check: 2026-10-22
    anchor_cutoff = datetime(2026, 10, 8, 0, 0, 0) # 14 days before anchor

    for lrn in learners:
        # Enrollment stats
        active_enrs = db.query(func.count(Enrollment.enrollment_id)).filter(
            Enrollment.learner_id == lrn.learner_id,
            Enrollment.enrollment_status == "ACTIVE"
        ).scalar() or 0
        completed_enrs = db.query(func.count(Enrollment.enrollment_id)).filter(
            Enrollment.learner_id == lrn.learner_id,
            Enrollment.enrollment_status == "COMPLETED"
        ).scalar() or 0

        # Risk scoring
        risk = "LOW"
        if active_enrs > 0:
            last_event_ts = db.query(func.max(ActivityEvent.event_timestamp_utc)).filter(
                ActivityEvent.learner_id == lrn.learner_id
            ).scalar()
            if not last_event_ts or last_event_ts < anchor_cutoff:
                risk = "HIGH"
            else:
                # Check assessment failure
                has_failed = db.query(Attempt.attempt_id).join(Enrollment, Attempt.enrollment_id == Enrollment.enrollment_id).filter(
                    Enrollment.learner_id == lrn.learner_id,
                    Attempt.attempt_status == "FAILED"
                ).first()
                if has_failed:
                    risk = "MEDIUM"

        items.append(LearnerListItem(
            learner_id=lrn.learner_id,
            full_name=f"{lrn.first_name} {lrn.last_name}",
            email=lrn.email,
            region=lrn.region,
            learning_mode=lrn.learning_mode,
            learner_status=lrn.learner_status,
            registration_date=lrn.registration_date.isoformat(),
            active_enrollment_count=active_enrs,
            completed_enrollment_count=completed_enrs,
            overall_risk_level=risk,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{learner_id}",
    response_model=LearnerDetail,
    summary="Get learner profile with enrollments and explainable outcomes",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF, Roles.LEARNER))]
)
def get_learner_detail(
    learner_id: str = Path(..., description="Target Learner ID"),
    db: Session = Depends(get_db)
):
    """Retrieves full learner profile including courses, historical outcomes, and risk factors."""
    lrn = db.query(Learner).filter(Learner.learner_id == learner_id).first()
    if not lrn:
        raise HTTPException(status_code=404, detail=f"Learner '{learner_id}' not found.")

    enrollments = (
        db.query(Enrollment, Course.course_name, Cohort.cohort_name)
        .join(Course, Enrollment.course_id == Course.course_id)
        .join(Cohort, Enrollment.cohort_id == Cohort.cohort_id)
        .filter(Enrollment.learner_id == learner_id)
        .all()
    )

    enr_list = []
    risk_factors = []
    anchor_cutoff = datetime(2026, 10, 8, 0, 0, 0)

    for enr, cname, cohname in enrollments:
        current_outcome = (
            db.query(CourseOutcome)
            .filter(CourseOutcome.enrollment_id == enr.enrollment_id, CourseOutcome.is_current == True)
            .first()
        )

        explainable_payload = None
        if current_outcome:
            try:
                explainable_payload = json.loads(current_outcome.outcome_reason)
            except Exception:
                explainable_payload = {"raw_explanation": current_outcome.outcome_reason}

        # Check last active event
        last_evt = db.query(func.max(ActivityEvent.event_timestamp_utc)).filter(
            ActivityEvent.enrollment_id == enr.enrollment_id
        ).scalar()
        if enr.enrollment_status == "ACTIVE" and (not last_evt or last_evt < anchor_cutoff):
            risk_factors.append(f"No activity in course '{cname}' in past 14 days.")

        c_pct = float(current_outcome.content_completion_percentage) if current_outcome else 0.0
        a_pct = float(current_outcome.assessment_progress_percentage) if current_outcome else 0.0
        f_score = float(current_outcome.final_assessment_score) if current_outcome and current_outcome.final_assessment_score is not None else None

        enr_list.append(EnrollmentOverview(
            enrollment_id=enr.enrollment_id,
            course_id=enr.course_id,
            course_name=cname,
            cohort_name=cohname,
            enrolled_at=enr.enrolled_at.isoformat(),
            enrollment_status=enr.enrollment_status,
            content_completion_percentage=c_pct,
            assessment_progress_percentage=a_pct,
            final_assessment_score=f_score,
            outcome_status=current_outcome.completion_status if current_outcome else None,
            outcome_version=current_outcome.outcome_version if current_outcome else None,
            explainable_outcome=explainable_payload,
        ))

    overall_risk = "HIGH" if len(risk_factors) >= 2 else ("MEDIUM" if len(risk_factors) == 1 else "LOW")

    return LearnerDetail(
        learner_id=lrn.learner_id,
        first_name=lrn.first_name,
        last_name=lrn.last_name,
        full_name=f"{lrn.first_name} {lrn.last_name}",
        email=lrn.email,
        region=lrn.region,
        learning_mode=lrn.learning_mode,
        learner_status=lrn.learner_status,
        registration_date=lrn.registration_date.isoformat(),
        overall_risk_level=overall_risk,
        risk_factors=risk_factors,
        enrollments=enr_list,
    )


@router.get(
    "/{learner_id}/activity",
    response_model=PaginatedResponse[LearnerActivityItem],
    summary="Get chronological event stream for a learner",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF, Roles.LEARNER))]
)
def get_learner_activity(
    learner_id: str = Path(..., description="Target Learner ID"),
    course_id: Optional[str] = Query(None, description="Filter by course"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieves paginated audit log of learner activity events ordered chronologically."""
    query = db.query(ActivityEvent).filter(ActivityEvent.learner_id == learner_id)

    if course_id:
        query = query.filter(ActivityEvent.course_id == course_id)
    if event_type:
        query = query.filter(ActivityEvent.event_type == event_type.upper())

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    events = query.order_by(ActivityEvent.event_timestamp_utc.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = [
        LearnerActivityItem(
            event_id=e.event_id,
            course_id=e.course_id,
            content_id=e.content_id,
            event_type=e.event_type,
            event_timestamp_utc=e.event_timestamp_utc.isoformat(),
            local_event_date=e.event_date.isoformat(),
            source_timezone=e.source_timezone,
            device_type=e.device_type,
            sync_status=e.sync_status,
        )
        for e in events
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
