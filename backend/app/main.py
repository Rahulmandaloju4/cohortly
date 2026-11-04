"""Cohortly – Learning Analytics & Cohort Intelligence Platform
Backend Application Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cohortly")

app = FastAPI(
    title="Cohortly – Learning Analytics & Cohort Intelligence Platform",
    description="Turn learning data into actionable intelligence.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def demo_role_middleware(request: Request, call_next):
    """Inspects X-Demo-Role and X-Demo-Learner-Id headers (defaults to PLATFORM_ADMIN and LRN-000001 if omitted)."""
    role = request.headers.get("X-Demo-Role", "PLATFORM_ADMIN").upper()
    request.state.role = role
    learner_id = request.headers.get("X-Demo-Learner-Id", "LRN-000001")
    request.state.learner_id = learner_id
    response = await call_next(request)
    response.headers["X-Demo-Role-Applied"] = role
    response.headers["X-Demo-Learner-Id-Applied"] = learner_id
    return response


# Include API Routers
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.learners import router as learners_router
from backend.app.api.courses import router as courses_router
from backend.app.api.cohorts import router as cohorts_router
from backend.app.api.assessments import router as assessments_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.exceptions import router as exceptions_router
from backend.app.api.data import router as data_router
from backend.app.core.rbac import require_roles, Roles
from backend.app.core.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

app.include_router(dashboard_router)
app.include_router(learners_router)
app.include_router(courses_router)
app.include_router(cohorts_router)
app.include_router(assessments_router)
app.include_router(analytics_router)
app.include_router(exceptions_router)
app.include_router(data_router)


# Backwards-compatible aliases for /api/audit routes referencing data endpoints
@app.get("/api/audit/benchmark", tags=["Audit"], dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN))])
def audit_benchmark_alias(db: Session = Depends(get_db)):
    """Backwards-compatible alias for GET /api/data/benchmark."""
    from backend.app.api.data import get_detection_benchmark
    return get_detection_benchmark(db=db)


@app.get("/api/audit/validation-report", tags=["Audit"], dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN))])
def audit_validation_report_alias(force: bool = False, db: Session = Depends(get_db)):
    """Backwards-compatible alias for GET /api/data/validation."""
    from backend.app.api.data import get_data_validation
    return get_data_validation(force=force, db=db)


@app.on_event("startup")
def prewarm_caches():
    """Pre-warms dashboard trends on server startup so initial UI loads are instantaneous."""
    try:
        from backend.app.core.database import SessionLocal
        from backend.app.api.dashboard import get_engagement_trend, get_completion_trend
        from backend.app.api.analytics import get_engagement_analytics
        db = SessionLocal()
        try:
            get_engagement_trend(weeks=6, db=db)
            get_completion_trend(db=db)
            get_engagement_analytics(db=db)
            logger.info("Dashboard trend and analytics caches pre-warmed successfully.")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Dashboard cache pre-warm skipped: {e}")


@app.get("/api/health", tags=["System"])
async def health_check():
    """System health check and diagnostic connectivity endpoint."""
    return {
        "status": "healthy",
        "platform": "Cohortly",
        "tagline": "Turn learning data into actionable intelligence.",
        "version": "1.0.0",
        "database": "sqlite_ready",
        "active_profile": "starter",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
