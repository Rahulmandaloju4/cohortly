"""Aggregated engagement, completion, and content usage analytics schemas."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class BreakdownSegment(BaseModel):
    segment: str
    active_count: int
    eligible_count: int
    rate: float


class EngagementAnalytics(BaseModel):
    overall_waler: float
    overall_waeer: float
    by_region: List[BreakdownSegment]
    by_device: List[BreakdownSegment]
    by_learning_mode: List[BreakdownSegment]


class CompletionAnalytics(BaseModel):
    overall_completion_rate: float
    by_category: List[BreakdownSegment]
    by_program_type: List[BreakdownSegment]
    by_difficulty: List[BreakdownSegment]


class ContentUsageItem(BaseModel):
    sequence_number: int
    content_id: str
    course_name: str
    title: str
    content_type: str
    views_count: int
    estimated_duration_minutes: int
    avg_session_duration_minutes: float
    drop_off_pct: float
