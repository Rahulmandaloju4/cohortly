"""Synthetic data management, validation audit, manifest, export, and evaluation benchmark API endpoints.
"""

import os
import io
import csv
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from backend.app.core.database import get_db, settings
from backend.app.core.rbac import require_roles, Roles
from backend.app.schemas.data import GenerateRequest, DataStatusResponse, TableStatus, ManifestResponse, ManifestEntry
from backend.app.schemas.common import MessageResponse
from backend.app.generators.generate import generate_dataset
from backend.app.validators.integrity_validator import run_15_point_validation
from backend.app.eval.benchmark import evaluate_detection_benchmark
from backend.app.services.anomaly_detector import scan_and_register_anomalies

router = APIRouter(prefix="/api/data", tags=["Data Management"])

ALL_TABLES = [
    "instructors", "learners", "courses", "cohorts", "enrollments",
    "content_items", "activity_events", "assessments", "attempts",
    "completion_rules", "course_outcomes", "exceptions", "state_history"
]


@router.post(
    "/generate",
    response_model=MessageResponse,
    summary="Trigger deterministic synthetic data generation",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN))]
)
def trigger_generation(payload: GenerateRequest):
    """Executes deterministic dataset generation according to preset or custom parameters."""
    try:
        summary = generate_dataset(
            profile=payload.profile,
            seed=payload.seed,
            num_learners=payload.num_learners,
            num_courses=payload.num_courses,
            num_enrollments=payload.num_enrollments,
            num_events=payload.num_events,
            db_path="data/generated/cohortly.db",
            ground_truth_path="data/ground_truth/anomalies.json",
            quiet=True,
        )
        return MessageResponse(
            message=f"Synthetic dataset generation ({payload.profile}) completed in {summary['execution_time_seconds']}s with seed {payload.seed}.",
            status="success",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get(
    "/status",
    response_model=DataStatusResponse,
    summary="Get database file health, table row counts, and disk footprint",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN))]
)
def get_data_status(db: Session = Depends(get_db)):
    """Computes file size, row counts, and table storage estimates for the operational database."""
    db_file = "data/generated/cohortly.db"
    size_mb = 0.0
    mtime_str = None

    if os.path.exists(db_file):
        size_bytes = os.path.getsize(db_file)
        size_mb = round(size_bytes / (1024 * 1024), 2)
        mtime = os.path.getmtime(db_file)
        mtime_str = datetime.fromtimestamp(mtime).isoformat() + "Z"

    table_statuses = []
    total_records = 0

    for tbl in ALL_TABLES:
        cnt = db.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar() or 0
        total_records += cnt
        # Approximate size based on average bytes per row
        est_kb = round((cnt * 128) / 1024, 2)
        table_statuses.append(TableStatus(
            table_name=tbl,
            row_count=cnt,
            size_estimate_kb=est_kb,
        ))

    profile = "starter" if total_records < 200000 else "full"

    return DataStatusResponse(
        database_file=db_file,
        database_size_mb=size_mb,
        last_generated_at=mtime_str,
        active_profile=profile,
        total_records=total_records,
        tables=table_statuses,
    )


@router.get(
    "/validation",
    summary="Execute complete 15-point cross-entity validation audit",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN))]
)
def get_data_validation(db: Session = Depends(get_db)):
    """Executes the full 15-point relational, lifecycle, and integrity audit suite."""
    report = run_15_point_validation(db)
    return report


@router.get(
    "/manifest",
    response_model=ManifestResponse,
    summary="Generate SHA-256 table manifests and row checksums",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN))]
)
def get_data_manifest(db: Session = Depends(get_db)):
    """Calculates deterministic SHA-256 content checksums for all 13 operational tables."""
    now_str = datetime.utcnow().isoformat() + "Z"
    entries = []

    for tbl in ALL_TABLES:
        rows = db.execute(text(f"SELECT * FROM {tbl} ORDER BY rowid ASC")).fetchall()
        hasher = hashlib.sha256()
        for r in rows:
            hasher.update(str(r).encode("utf-8"))
        checksum = hasher.hexdigest()

        entries.append(ManifestEntry(
            table_name=tbl,
            row_count=len(rows),
            sha256_checksum=checksum,
        ))

    return ManifestResponse(
        generated_at=now_str,
        seed=20261022,
        profile="starter",
        total_tables=len(entries),
        tables=entries,
    )


@router.get(
    "/benchmark",
    summary="Execute decoupled precision, recall, and F1 scorecard",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN))]
)
def get_detection_benchmark(db: Session = Depends(get_db)):
    """Runs decoupled evaluation comparing operational exceptions table against the isolated ground truth."""
    # Ensure fresh operational scan
    scan_and_register_anomalies(db)
    scorecard = evaluate_detection_benchmark(db)
    return scorecard


@router.get(
    "/export/{format}",
    summary="Export table data or analytics report as CSV or JSON stream",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN))]
)
def export_dataset(
    format: str = Path(..., pattern="^(csv|json)$"),
    table: str = Query("learners", description="Table name to export"),
    db: Session = Depends(get_db)
):
    """Streams table records formatted as standard RFC 4180 CSV or formatted JSON."""
    if table not in ALL_TABLES:
        raise HTTPException(status_code=400, detail=f"Invalid table '{table}'. Allowed: {', '.join(ALL_TABLES)}.")

    cursor_res = db.execute(text(f"SELECT * FROM {table}"))
    columns = list(cursor_res.keys())
    rows = cursor_res.fetchall()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        for r in rows:
            writer.writerow(list(r))
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=cohortly_{table}.csv"}
        )
    else:  # json
        data = [dict(zip(columns, list(r))) for r in rows]
        # serialize datetime/date to str
        def default_serializer(o):
            if isinstance(o, (datetime, date)):
                return o.isoformat()
            return str(o)
        json_str = json.dumps(data, indent=2, default=default_serializer)
        return StreamingResponse(
            iter([json_str]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=cohortly_{table}.json"}
        )
