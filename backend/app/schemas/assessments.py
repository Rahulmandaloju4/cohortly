"""Assessment and evaluation progress schemas."""
from typing import List, Optional, Any
from pydantic import BaseModel


class AssessmentItem(BaseModel):
    assessment_id: str
    course_id: str
    course_name: str
    title: str
    assessment_type: str
    max_score: float
    passing_score: float
    is_required: bool
    due_date: Optional[str]
    total_attempts: int
    pass_rate: float
    avg_score: Optional[float]


class LearnerAssessmentProgress(BaseModel):
    attempt_id: str
    assessment_id: str
    assessment_title: str
    course_id: str
    learner_id: str
    learner_name: str
    attempt_number: int
    score: Optional[float]
    max_score: float
    passing_score: float
    attempt_status: str
    submitted_at: str
    graded_at: Optional[str]
