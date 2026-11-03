"""Exception and data quality investigator schemas."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ExceptionListItem(BaseModel):
    exception_id: str
    issue_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    entity_type: str
    entity_id: str
    detected_at: str
    description: str
    resolution_status: str  # OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE


class ExceptionDetail(BaseModel):
    exception_id: str
    issue_type: str
    severity: str
    entity_type: str
    entity_id: str
    detected_at: str
    description: str
    evidence: Dict[str, Any]
    relevant_rule: str
    recommended_action: str
    resolution_status: str


class ExceptionStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(OPEN|INVESTIGATING|RESOLVED|FALSE_POSITIVE)$")
    reason: str = Field(..., min_length=3)
    actor_id: Optional[str] = "DEMO-USER"
