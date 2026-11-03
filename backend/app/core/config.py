"""Cohortly platform application configuration."""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Cohortly – Learning Analytics & Cohort Intelligence Platform"
    TAGLINE: str = "Turn learning data into actionable intelligence."
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/generated/cohortly.db"
    
    # Deterministic Reference Clock Anchor
    REFERENCE_ANCHOR_DATE: str = "2026-10-22T00:00:00Z"
    DEFAULT_SEED: int = 20261022
    
    # Starter Presets
    STARTER_LEARNERS: int = 200
    STARTER_INSTRUCTORS: int = 20
    STARTER_COURSES: int = 20
    STARTER_COHORTS: int = 10
    STARTER_ENROLLMENTS: int = 500
    STARTER_EVENTS: int = 10000
    
    # Full Presets
    FULL_LEARNERS: int = 20000
    FULL_INSTRUCTORS: int = 200
    FULL_COURSES: int = 500
    FULL_COHORTS: int = 50
    FULL_ENROLLMENTS: int = 100000
    FULL_EVENTS: int = 2000000
    
    # Thresholds
    NEAR_DUPLICATE_WINDOW_SECONDS: float = 5.0
    INACTIVITY_THRESHOLD_DAYS: int = 14
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "*"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
