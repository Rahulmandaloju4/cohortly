"""Cohort management and comparative analytics schemas."""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class CohortListItem(BaseModel):
    cohort_id: str
    cohort_name: str
    region: str
    program_type: str
    start_date: str
    end_date: str
    total_enrollments: int
    completion_rate: float
    status: str  # ACTIVE, UPCOMING, CONCLUDED


class CohortAnalytics(BaseModel):
    cohort_id: str
    cohort_name: str
    region: str
    program_type: str
    start_date: str
    end_date: str
    total_enrollments: int
    completed_count: int
    active_count: int
    dropped_count: int
    completion_rate: float
    waler: float
    waeer: float
    risk_distribution: Dict[str, int]  # LOW: n, MEDIUM: n, HIGH: n


class NormalizedTimelinePoint(BaseModel):
    day_number: int  # Day 0, Day 7, Day 14, ...
    metric_value: float


class CohortComparisonItem(BaseModel):
    cohort_id: str
    cohort_name: str
    program_type: str
    total_enrollments: int
    completion_rate: float
    waler: float
    average_score: Optional[float]
    engagement_timeline: List[NormalizedTimelinePoint]


class CohortComparisonResponse(BaseModel):
    cohorts: List[CohortComparisonItem]
