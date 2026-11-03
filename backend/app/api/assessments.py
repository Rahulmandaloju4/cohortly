"""Assessments and student evaluation progress API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from backend.app.core.database import get_db
from backend.app.core.rbac import require_roles, Roles
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.assessments import AssessmentItem, LearnerAssessmentProgress
from backend.app.models import Assessment, Course, Attempt, Enrollment, Learner

router = APIRouter(prefix="/api/assessments", tags=["Assessments"])


@router.get(
    "",
    response_model=List[AssessmentItem],
    summary="List assessments with pass rates and score metrics",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF, Roles.LEARNER))]
)
def list_assessments(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    assessment_type: Optional[str] = Query(None, description="Filter by type: QUIZ, EXAM, PROJECT, ASSIGNMENT"),
    db: Session = Depends(get_db)
):
    """Retrieves assessment catalog with aggregate attempt count and pass rate."""
    query = db.query(Assessment, Course.course_name).join(Course, Assessment.course_id == Course.course_id)

    if course_id:
        query = query.filter(Assessment.course_id == course_id)
    if assessment_type:
        query = query.filter(Assessment.assessment_type == assessment_type.upper())

    results = query.order_by(Assessment.created_at.desc()).all()
    items = []

    for asm, cname in results:
        attempts_q = db.query(Attempt).filter(Attempt.assessment_id == asm.assessment_id)
        total_att = attempts_q.count()
        passed_att = attempts_q.filter(Attempt.attempt_status == "PASSED").count()
        pass_rate = round((passed_att / total_att) * 100.0, 2) if total_att > 0 else 0.0

        avg_score = db.query(func.avg(Attempt.score)).filter(
            Attempt.assessment_id == asm.assessment_id,
            Attempt.score.is_not(None)
        ).scalar()
        avg_score_val = round(float(avg_score), 2) if avg_score is not None else None

        items.append(AssessmentItem(
            assessment_id=asm.assessment_id,
            course_id=asm.course_id,
            course_name=cname,
            title=asm.title,
            assessment_type=asm.assessment_type,
            max_score=float(asm.max_score),
            passing_score=float(asm.passing_score),
            is_required=asm.is_required,
            due_date=asm.due_date.isoformat() if asm.due_date else None,
            total_attempts=total_att,
            pass_rate=pass_rate,
            avg_score=avg_score_val,
        ))

    return items


@router.get(
    "/progress",
    response_model=PaginatedResponse[LearnerAssessmentProgress],
    summary="Get granular learner assessment attempts and scores",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF))]
)
def get_assessment_progress(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    assessment_id: Optional[str] = Query(None, description="Filter by assessment ID"),
    learner_id: Optional[str] = Query(None, description="Filter by learner ID"),
    status: Optional[str] = Query(None, description="Filter by attempt status: PASSED, FAILED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieves paginated list of individual assessment attempts with pass/fail evaluation."""
    query = (
        db.query(
            Attempt,
            Assessment.title,
            Assessment.max_score,
            Assessment.passing_score,
            Enrollment.course_id,
            Enrollment.learner_id,
            Learner.first_name,
            Learner.last_name,
        )
        .join(Assessment, Attempt.assessment_id == Assessment.assessment_id)
        .join(Enrollment, Attempt.enrollment_id == Enrollment.enrollment_id)
        .join(Learner, Enrollment.learner_id == Learner.learner_id)
    )

    if course_id:
        query = query.filter(Enrollment.course_id == course_id)
    if assessment_id:
        query = query.filter(Attempt.assessment_id == assessment_id)
    if learner_id:
        query = query.filter(Enrollment.learner_id == learner_id)
    if status:
        query = query.filter(Attempt.attempt_status == status.upper())

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    rows = query.order_by(Attempt.submitted_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = [
        LearnerAssessmentProgress(
            attempt_id=att.attempt_id,
            assessment_id=att.assessment_id,
            assessment_title=atitle,
            course_id=cid,
            learner_id=lid,
            learner_name=f"{lfirst} {llast}",
            attempt_number=att.attempt_number,
            score=float(att.score) if att.score is not None else None,
            max_score=float(amax),
            passing_score=float(apass),
            attempt_status=att.attempt_status,
            submitted_at=att.submitted_at.isoformat(),
            graded_at=att.graded_at.isoformat() if att.graded_at else None,
        )
        for att, atitle, amax, apass, cid, lid, lfirst, llast in rows
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
