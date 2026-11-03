"""Learner schemas."""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class LearnerListItem(BaseModel):
    learner_id: str
    full_name: str
    email: str
    region: str
    learning_mode: str
    learner_status: str
    registration_date: str
    active_enrollment_count: int
    completed_enrollment_count: int
    overall_risk_level: str  # LOW, MEDIUM, HIGH


class EnrollmentOverview(BaseModel):
    enrollment_id: str
    course_id: str
    course_name: str
    cohort_name: str
    enrolled_at: str
    enrollment_status: str
    content_completion_percentage: float
    assessment_progress_percentage: float
    final_assessment_score: Optional[float]
    outcome_status: Optional[str]
    outcome_version: Optional[int]
    explainable_outcome: Optional[Dict[str, Any]]


class LearnerDetail(BaseModel):
    learner_id: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    region: str
    learning_mode: str
    learner_status: str
    registration_date: str
    overall_risk_level: str
    risk_factors: List[str]
    enrollments: List[EnrollmentOverview]


class LearnerActivityItem(BaseModel):
    event_id: str
    course_id: str
    content_id: Optional[str]
    event_type: str
    event_timestamp_utc: str
    local_event_date: str
    source_timezone: str
    device_type: str
    sync_status: str
