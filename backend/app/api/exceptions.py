"""Exceptions and data quality investigator API endpoints.
Provides anomaly inspection, explainable JSON evidence payloads,
and state transitions that append to the immutable state_history audit table.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from backend.app.core.database import get_db
from backend.app.core.rbac import require_roles, Roles, get_current_role
from backend.app.schemas.common import PaginatedResponse, MessageResponse
from backend.app.schemas.exceptions import ExceptionListItem, ExceptionDetail, ExceptionStatusUpdate
from backend.app.models import ExceptionRecord, StateHistory
from backend.app.utils.ids import make_history_id

router = APIRouter(prefix="/api/exceptions", tags=["Exceptions"])


@router.get(
    "",
    response_model=PaginatedResponse[ExceptionListItem],
    summary="List detected exceptions and anomalies",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF))]
)
def list_exceptions(
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    issue_type: Optional[str] = Query(None, description="Filter by issue type"),
    resolution_status: Optional[str] = Query(None, description="Filter by status: OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieves paginated list of operational anomalies recorded in the exceptions ledger."""
    query = db.query(ExceptionRecord)

    if severity:
        query = query.filter(ExceptionRecord.severity == severity.upper())
    if issue_type:
        query = query.filter(ExceptionRecord.issue_type == issue_type)
    if resolution_status:
        query = query.filter(ExceptionRecord.resolution_status == resolution_status.upper())

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    rows = query.order_by(ExceptionRecord.detected_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = [
        ExceptionListItem(
            exception_id=e.exception_id,
            issue_type=e.issue_type,
            severity=e.severity,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            detected_at=e.detected_at.isoformat(),
            description=e.description,
            resolution_status=e.resolution_status,
        )
        for e in rows
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{exception_id}",
    response_model=ExceptionDetail,
    summary="Get exception inspection details with JSON evidence",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF))]
)
def get_exception_detail(
    exception_id: str = Path(..., description="Target Exception ID"),
    db: Session = Depends(get_db)
):
    """Retrieves complete forensic payload for an anomaly including evidence dictionary and remediation actions."""
    exc = db.query(ExceptionRecord).filter(ExceptionRecord.exception_id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail=f"Exception '{exception_id}' not found.")

    return ExceptionDetail(
        exception_id=exc.exception_id,
        issue_type=exc.issue_type,
        severity=exc.severity,
        entity_type=exc.entity_type,
        entity_id=exc.entity_id,
        detected_at=exc.detected_at.isoformat(),
        description=exc.description,
        evidence=exc.evidence,
        relevant_rule=exc.relevant_rule,
        recommended_action=exc.recommended_action,
        resolution_status=exc.resolution_status,
    )


@router.patch(
    "/{exception_id}/status",
    response_model=MessageResponse,
    summary="Update exception triage status with immutable audit logging",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN, Roles.INSTRUCTOR, Roles.SUPPORT_STAFF))]
)
def update_exception_status(
    payload: ExceptionStatusUpdate,
    exception_id: str = Path(..., description="Target Exception ID"),
    db: Session = Depends(get_db),
    current_role: str = Depends(get_current_role)
):
    """Transitions anomaly resolution status and appends an immutable entry to state_history."""
    exc = db.query(ExceptionRecord).filter(ExceptionRecord.exception_id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail=f"Exception '{exception_id}' not found.")

    prev_state = exc.resolution_status
    new_state = payload.status
    now = datetime.utcnow()

    if prev_state == new_state:
        return MessageResponse(message=f"Exception status is already '{new_state}'. No state transition recorded.")

    # 1. Update current state on exception entity
    exc.resolution_status = new_state

    # 2. Append immutable record to state_history
    hist_count = db.query(func.count(StateHistory.history_id)).scalar() or 0
    hist_id = make_history_id(hist_count + 1)

    history_record = StateHistory(
        history_id=hist_id,
        entity_type="EXCEPTION",
        entity_id=exc.exception_id,
        previous_state=prev_state,
        new_state=new_state,
        changed_at=now,
        actor_role=current_role,
        actor_id=payload.actor_id or "DEMO-USER",
        reason=payload.reason,
    )
    db.add(history_record)
    db.commit()

    return MessageResponse(
        message=f"Exception '{exception_id}' transitioned from '{prev_state}' to '{new_state}'. Audit event {hist_id} appended.",
        status="success",
        timestamp=now.isoformat() + "Z",
    )
