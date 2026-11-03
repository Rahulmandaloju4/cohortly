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
    """Inspects X-Demo-Role header (defaults to PLATFORM_ADMIN if omitted for demo)."""
    role = request.headers.get("X-Demo-Role", "PLATFORM_ADMIN").upper()
    request.state.role = role
    response = await call_next(request)
    response.headers["X-Demo-Role-Applied"] = role
    return response


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
