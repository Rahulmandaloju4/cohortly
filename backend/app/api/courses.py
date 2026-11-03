"""Courses and curriculum API endpoints.
Provides course directory, hierarchical content tree, and course-level engagement & drop-off analytics.
"""

from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from backend.app.core.database import get_db
from backend.app.core.rbac import require_roles, Roles
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.courses import CourseListItem, CourseDetail, ContentNode, CourseAnalytics, DropOffItem
from backend.app.models import Course, Instructor, ContentItem, CompletionRule, Enrollment, CourseOutcome, ActivityEvent

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get(
    "",
    response_model=PaginatedResponse[CourseListItem],
    summary="List courses with enrollment and completion statistics",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF, Roles.LEARNER))]
)
def list_courses(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: BEGINNER, INTERMEDIATE, ADVANCED"),
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, ARCHIVED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieves paginated course catalog with computed graduation rates."""
    query = db.query(Course, Instructor.first_name, Instructor.last_name).join(Instructor, Course.instructor_id == Instructor.instructor_id)

    if category:
        query = query.filter(Course.category == category)
    if difficulty:
        query = query.filter(Course.difficulty_level == difficulty.upper())
    if status:
        query = query.filter(Course.course_status == status.upper())

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    rows = query.order_by(Course.course_name.asc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for crs, ifirst, ilast in rows:
        total_enrs = db.query(func.count(Enrollment.enrollment_id)).filter(Enrollment.course_id == crs.course_id).scalar() or 0
        comp_enrs = db.query(func.count(Enrollment.enrollment_id)).filter(
            Enrollment.course_id == crs.course_id,
            Enrollment.enrollment_status == "COMPLETED"
        ).scalar() or 0
        comp_rate = round((comp_enrs / total_enrs) * 100.0, 2) if total_enrs > 0 else 0.0

        avg_score_q = text("""
            SELECT AVG(co.final_assessment_score)
            FROM course_outcomes co
            JOIN enrollments en ON co.enrollment_id = en.enrollment_id
            WHERE en.course_id = :cid AND co.is_current = 1 AND co.final_assessment_score IS NOT NULL
        """)
        avg_score = db.execute(avg_score_q, {"cid": crs.course_id}).scalar()
        avg_score_val = round(float(avg_score), 2) if avg_score is not None else None

        items.append(CourseListItem(
            course_id=crs.course_id,
            course_name=crs.course_name,
            category=crs.category,
            difficulty_level=crs.difficulty_level,
            instructor_name=f"{ifirst} {ilast}",
            course_status=crs.course_status,
            total_enrollments=total_enrs,
            completion_rate=comp_rate,
            avg_assessment_score=avg_score_val,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{course_id}",
    response_model=CourseDetail,
    summary="Get course curriculum tree and active completion rules",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF, Roles.LEARNER))]
)
def get_course_detail(
    course_id: str = Path(..., description="Target Course ID"),
    db: Session = Depends(get_db)
):
    """Retrieves full course profile including instructor, completion rule, and nested curriculum tree."""
    crs = db.query(Course).filter(Course.course_id == course_id).first()
    if not crs:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found.")

    ins = db.query(Instructor).filter(Instructor.instructor_id == crs.instructor_id).first()
    rule = db.query(CompletionRule).filter(CompletionRule.course_id == course_id, CompletionRule.is_active == True).first()

    rule_payload = None
    if rule:
        rule_payload = {
            "rule_id": rule.completion_rule_id,
            "rule_version": rule.rule_version,
            "minimum_content_completion_percentage": float(rule.minimum_content_completion_percentage),
            "minimum_assessment_score": float(rule.minimum_assessment_score),
            "require_all_mandatory_assessments": rule.require_all_mandatory_assessments,
            "effective_from": rule.effective_from.isoformat(),
        }

    # Fetch content items and construct nested hierarchy
    raw_contents = db.query(ContentItem).filter(ContentItem.course_id == course_id).order_by(ContentItem.sequence_number.asc()).all()

    # Build parent -> children map
    modules: List[ContentNode] = []
    lessons_by_parent: Dict[str, List[ContentNode]] = {}

    for item in raw_contents:
        node = ContentNode(
            content_id=item.content_id,
            title=item.title,
            content_type=item.content_type,
            sequence_number=item.sequence_number,
            estimated_duration_minutes=item.estimated_duration_minutes,
            is_required=item.is_required,
            children=[],
        )
        if item.parent_content_id is None:
            modules.append(node)
        else:
            lessons_by_parent.setdefault(item.parent_content_id, []).append(node)

    for mod in modules:
        mod.children = lessons_by_parent.get(mod.content_id, [])

    return CourseDetail(
        course_id=crs.course_id,
        course_name=crs.course_name,
        category=crs.category,
        difficulty_level=crs.difficulty_level,
        course_status=crs.course_status,
        instructor_id=ins.instructor_id,
        instructor_name=f"{ins.first_name} {ins.last_name}",
        instructor_email=ins.email,
        department=ins.department,
        created_at=crs.created_at.isoformat(),
        active_rule=rule_payload,
        curriculum=modules,
    )


@router.get(
    "/{course_id}/analytics",
    response_model=CourseAnalytics,
    summary="Get course graduation rates and content drop-off funnel",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR))]
)
def get_course_analytics(
    course_id: str = Path(..., description="Target Course ID"),
    db: Session = Depends(get_db)
):
    """Calculates enrollment funnel metrics and lesson-by-lesson retention / drop-off rates."""
    crs = db.query(Course).filter(Course.course_id == course_id).first()
    if not crs:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found.")

    total = db.query(func.count(Enrollment.enrollment_id)).filter(Enrollment.course_id == course_id).scalar() or 0
    active = db.query(func.count(Enrollment.enrollment_id)).filter(Enrollment.course_id == course_id, Enrollment.enrollment_status == "ACTIVE").scalar() or 0
    completed = db.query(func.count(Enrollment.enrollment_id)).filter(Enrollment.course_id == course_id, Enrollment.enrollment_status == "COMPLETED").scalar() or 0
    dropped = db.query(func.count(Enrollment.enrollment_id)).filter(Enrollment.course_id == course_id, Enrollment.enrollment_status == "DROPPED").scalar() or 0
    comp_rate = round((completed / total) * 100.0, 2) if total > 0 else 0.0

    avg_score_q = text("""
        SELECT AVG(co.final_assessment_score)
        FROM course_outcomes co
        JOIN enrollments en ON co.enrollment_id = en.enrollment_id
        WHERE en.course_id = :cid AND co.is_current = 1 AND co.final_assessment_score IS NOT NULL
    """)
    avg_score = db.execute(avg_score_q, {"cid": course_id}).scalar()
    avg_score_val = round(float(avg_score), 2) if avg_score is not None else None

    # Drop-off funnel: for each content item, count distinct enrollments reaching it
    content_items = db.query(ContentItem).filter(ContentItem.course_id == course_id).order_by(ContentItem.sequence_number.asc()).all()
    funnel = []
    prev_reach = total or 1

    for c in content_items:
        reach_q = text("""
            SELECT COUNT(DISTINCT enrollment_id)
            FROM activity_events
            WHERE course_id = :cid AND content_id = :cont_id AND enrollment_id IS NOT NULL
        """)
        reached = db.execute(reach_q, {"cid": course_id, "cont_id": c.content_id}).scalar() or 0
        drop_rate = round(((prev_reach - reached) / prev_reach) * 100.0, 2) if prev_reach > 0 and reached < prev_reach else 0.0
        prev_reach = max(reached, 1)

        funnel.append(DropOffItem(
            sequence_number=c.sequence_number,
            content_id=c.content_id,
            title=c.title,
            content_type=c.content_type,
            learners_reached=reached,
            drop_off_rate_percent=drop_rate,
        ))

    return CourseAnalytics(
        course_id=crs.course_id,
        course_name=crs.course_name,
        total_enrolled=total,
        active_count=active,
        completed_count=completed,
        dropped_count=dropped,
        completion_rate=comp_rate,
        avg_final_score=avg_score_val,
        drop_off_funnel=funnel,
    )
