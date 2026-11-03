"""Dashboard analytics schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class AnomalyBreakdownItem(BaseModel):
    issue_type: str
    count: int
    severity: str
    description: str


class OverviewMetrics(BaseModel):
    total_learners: int
    active_learners: int
    total_courses: int
    active_cohorts: int
    total_enrollments: int
    waler: float  # Weekly Active Learner Engagement Rate (%)
    waeer: float  # Weekly Active Enrollment Engagement Rate (%)
    overall_completion_rate: float
    at_risk_learner_count: int
    active_anomaly_count: int
    active_anomalies_breakdown: List[AnomalyBreakdownItem] = []
    total_activity_events: int
    deduplicated_events: int


class EngagementTrendPoint(BaseModel):
    period_start: str
    period_end: str
    label: str
    distinct_active_learners: int
    eligible_learners: int
    waler: float
    distinct_active_enrollments: int
    eligible_enrollments: int
    waeer: float


class CompletionTrendPoint(BaseModel):
    cohort_id: str
    cohort_name: str
    total_enrollments: int
    completed_count: int
    completion_rate: float
    avg_score: Optional[float]
