"""Course curriculum and analytics schemas."""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class CourseListItem(BaseModel):
    course_id: str
    course_name: str
    category: str
    difficulty_level: str
    instructor_name: str
    course_status: str
    total_enrollments: int
    completion_rate: float
    avg_assessment_score: Optional[float]


class ContentNode(BaseModel):
    content_id: str
    title: str
    content_type: str
    sequence_number: int
    estimated_duration_minutes: int
    is_required: bool
    children: List["ContentNode"] = []


class CourseDetail(BaseModel):
    course_id: str
    course_name: str
    category: str
    difficulty_level: str
    course_status: str
    instructor_id: str
    instructor_name: str
    instructor_email: str
    department: str
    created_at: str
    active_rule: Optional[Dict[str, Any]]
    curriculum: List[ContentNode]


class DropOffItem(BaseModel):
    sequence_number: int
    content_id: str
    title: str
    content_type: str
    learners_reached: int
    drop_off_rate_percent: float


class CourseAnalytics(BaseModel):
    course_id: str
    course_name: str
    total_enrolled: int
    active_count: int
    completed_count: int
    dropped_count: int
    completion_rate: float
    avg_final_score: Optional[float]
    drop_off_funnel: List[DropOffItem]
