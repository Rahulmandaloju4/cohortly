"""Synthetic data generator, system status, validation, and manifest schemas."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    profile: str = Field("starter", pattern="^(starter|full)$")
    seed: int = Field(20261022, ge=1)
    num_learners: Optional[int] = None
    num_courses: Optional[int] = None
    num_enrollments: Optional[int] = None
    num_events: Optional[int] = None


class TableStatus(BaseModel):
    table_name: str
    row_count: int
    size_estimate_kb: float


class DataStatusResponse(BaseModel):
    database_file: str
    database_size_mb: float
    last_generated_at: Optional[str]
    active_profile: str
    total_records: int
    tables: List[TableStatus]


class ManifestEntry(BaseModel):
    table_name: str
    row_count: int
    sha256_checksum: str


class ManifestResponse(BaseModel):
    generated_at: str
    seed: int
    profile: str
    total_tables: int
    tables: List[ManifestEntry]
