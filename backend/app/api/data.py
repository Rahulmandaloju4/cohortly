"""Synthetic data management, validation audit, manifest, export, and evaluation benchmark API endpoints.
"""

import os
import io
import csv
import json
import hashlib
from datetime import datetime, date
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


DATASET_VERSION_PATH = "data/manifests/dataset_version.json"
MANIFEST_CACHE_PATH = "data/manifests/table_manifest.json"
VALIDATION_CACHE_PATH = "data/manifests/validation_report.json"
BENCHMARK_CACHE_PATH = "data/manifests/benchmark_scorecard.json"


def get_dataset_fingerprint(db_file: str = "data/generated/cohortly.db") -> str:
    """Computes a lightweight fingerprint based on operational database file size and mtime."""
    if not os.path.exists(db_file):
        return "no_db"
    try:
        size_bytes = os.path.getsize(db_file)
        mtime = os.path.getmtime(db_file)
        return f"{size_bytes}_{mtime}"
    except OSError:
        return "err_db"


def get_dataset_version() -> Dict[str, Any]:
    """Retrieves dataset version lifecycle metadata, initializing default if not present."""
    if os.path.exists(DATASET_VERSION_PATH):
        try:
            with open(DATASET_VERSION_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Fallback initialization based on db presence
    db_file = "data/generated/cohortly.db"
    if os.path.exists(db_file):
        fp = get_dataset_fingerprint(db_file)
        default_ver = {
            "generation_id": f"gen_existing_{fp}",
            "profile": "full",
            "seed": 20261022,
            "status": "READY",
            "db_fingerprint": fp,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
        set_dataset_version(default_ver)
        return default_ver
    return {"status": "NO_DATASET", "generation_id": None}


def set_dataset_version(version_data: Dict[str, Any]) -> None:
    """Atomically writes dataset version lifecycle metadata."""
    try:
        parent = os.path.dirname(DATASET_VERSION_PATH)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp_p = f"{DATASET_VERSION_PATH}.tmp"
        with open(tmp_p, "w", encoding="utf-8") as f:
            json.dump(version_data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_p, DATASET_VERSION_PATH)
    except Exception as e:
        print(f"Warning: Failed to write dataset version: {e}")


def get_cached_json(cache_path: str, expected_gen_id: str) -> Optional[Dict[str, Any]]:
    """Reads cached JSON payload if file exists and matches the expected dataset generation ID."""
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("_dataset_generation_id") == expected_gen_id or data.get("_dataset_fingerprint") == expected_gen_id:
            return data.get("payload")
    except Exception:
        return None
    return None


def set_cached_json(cache_path: str, gen_id: str, payload: Dict[str, Any]) -> None:
    """Atomically writes cached JSON payload using a temporary file and os.replace."""
    try:
        parent = os.path.dirname(cache_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp_path = f"{cache_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump({
                "_dataset_generation_id": gen_id,
                "_dataset_fingerprint": gen_id,
                "cached_at": datetime.utcnow().isoformat() + "Z",
                "payload": payload
            }, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, cache_path)
    except Exception as e:
        print(f"Warning: Failed to write cache to {cache_path}: {e}")


def invalidate_all_caches() -> None:
    """Removes existing cache and temporary files upon new dataset generation."""
    for p in [MANIFEST_CACHE_PATH, VALIDATION_CACHE_PATH, BENCHMARK_CACHE_PATH]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass
        tmp_p = f"{p}.tmp"
        if os.path.exists(tmp_p):
            try:
                os.remove(tmp_p)
            except OSError:
                pass


def compute_table_manifest(db: Session) -> ManifestResponse:
    """Calculates deterministic SHA-256 content checksums for all 13 operational tables."""
    now_str = datetime.utcnow().isoformat() + "Z"
    entries = []

    for tbl in ALL_TABLES:
        cnt = db.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar() or 0
        hasher = hashlib.sha256()
        cursor = db.connection().connection.cursor()
        try:
            cursor.execute(f"SELECT * FROM {tbl} ORDER BY rowid ASC")
            while True:
                chunk = cursor.fetchmany(10000)
                if not chunk:
                    break
                for r in chunk:
                    hasher.update(str(r).encode("utf-8"))
        finally:
            cursor.close()
        checksum = hasher.hexdigest()

        entries.append(ManifestEntry(
            table_name=tbl,
            row_count=cnt,
            sha256_checksum=checksum,
        ))

    total_records = sum(e.row_count for e in entries)
    profile = "starter" if total_records < 200000 else "full"

    return ManifestResponse(
        generated_at=now_str,
        seed=20261022,
        profile=profile,
        total_tables=len(entries),
        tables=entries,
    )


@router.post(
    "/generate",
    response_model=MessageResponse,
    summary="Trigger deterministic synthetic data generation",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN))]
)
def trigger_generation(payload: GenerateRequest, db: Session = Depends(get_db)):
    """Executes deterministic dataset generation according to preset or custom parameters."""
    # 1. Mark generation in progress and clear stale caches
    set_dataset_version({
        "status": "GENERATING",
        "generation_id": None,
        "profile": payload.profile,
        "seed": payload.seed,
        "started_at": datetime.utcnow().isoformat() + "Z",
    })
    invalidate_all_caches()

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

        # 2. On generation success, establish new dataset generation ID
        new_gen_id = f"gen_{payload.profile}_{payload.seed}_{int(datetime.utcnow().timestamp())}"
        set_dataset_version({
            "status": "READY",
            "generation_id": new_gen_id,
            "profile": payload.profile,
            "seed": payload.seed,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "db_fingerprint": get_dataset_fingerprint("data/generated/cohortly.db"),
            "execution_time_seconds": summary.get("execution_time_seconds"),
        })

        # 3. Pre-populate and atomically cache validation, manifest, and benchmark results
        try:
            val_rep = run_15_point_validation(db)
            set_cached_json(VALIDATION_CACHE_PATH, new_gen_id, val_rep)
        except Exception as ex:
            print(f"Warning: post-generation validation caching failed: {ex}")

        try:
            manifest = compute_table_manifest(db)
            manifest_dict = manifest.model_dump() if hasattr(manifest, "model_dump") else manifest.dict()
            set_cached_json(MANIFEST_CACHE_PATH, new_gen_id, manifest_dict)
        except Exception as ex:
            print(f"Warning: post-generation manifest caching failed: {ex}")

        try:
            scorecard = evaluate_detection_benchmark(db)
            set_cached_json(BENCHMARK_CACHE_PATH, new_gen_id, scorecard)
        except Exception as ex:
            print(f"Warning: post-generation benchmark caching failed: {ex}")

        return MessageResponse(
            message=f"Synthetic dataset generation ({payload.profile}) completed in {summary['execution_time_seconds']}s with seed {payload.seed}.",
            status="success",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        # 4. On generation failure, record failed state and ensure stale caches are purged
        set_dataset_version({
            "status": "FAILED",
            "generation_id": None,
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat() + "Z",
        })
        invalidate_all_caches()
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
def get_data_validation(
    force: bool = Query(False, description="Bypass cache and force full recalculation"),
    db: Session = Depends(get_db)
):
    """Executes the full 15-point relational, lifecycle, and integrity audit suite."""
    version = get_dataset_version()
    if version.get("status") == "GENERATING":
        raise HTTPException(
            status_code=409,
            detail="Dataset generation is currently in progress. Validation audit is temporarily unavailable."
        )
    if version.get("status") == "FAILED":
        raise HTTPException(
            status_code=500,
            detail=f"Database is in an invalid state due to previous generation failure: {version.get('error')}. Please trigger data generation again."
        )

    gen_id = version.get("generation_id") or get_dataset_fingerprint()
    if not force and gen_id:
        cached = get_cached_json(VALIDATION_CACHE_PATH, gen_id)
        if cached is not None:
            return cached

    report = run_15_point_validation(db)
    if gen_id:
        set_cached_json(VALIDATION_CACHE_PATH, gen_id, report)
    return report


@router.get(
    "/manifest",
    response_model=ManifestResponse,
    summary="Generate SHA-256 table manifests and row checksums",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN))]
)
def get_data_manifest(
    force: bool = Query(False, description="Bypass cache and force full recalculation"),
    db: Session = Depends(get_db)
):
    """Calculates deterministic SHA-256 content checksums for all 13 operational tables."""
    version = get_dataset_version()
    if version.get("status") == "GENERATING":
        raise HTTPException(
            status_code=409,
            detail="Dataset generation is currently in progress. Table manifest is temporarily unavailable."
        )
    if version.get("status") == "FAILED":
        raise HTTPException(
            status_code=500,
            detail=f"Database is in an invalid state due to previous generation failure: {version.get('error')}. Please trigger data generation again."
        )

    gen_id = version.get("generation_id") or get_dataset_fingerprint()
    if not force and gen_id:
        cached = get_cached_json(MANIFEST_CACHE_PATH, gen_id)
        if cached is not None:
            return cached

    manifest = compute_table_manifest(db)
    manifest_dict = manifest.model_dump() if hasattr(manifest, "model_dump") else manifest.dict()
    if gen_id:
        set_cached_json(MANIFEST_CACHE_PATH, gen_id, manifest_dict)
    return manifest


@router.get(
    "/benchmark",
    summary="Execute decoupled precision, recall, and F1 scorecard",
    dependencies=[Depends(require_roles(Roles.PLATFORM_ADMIN, Roles.ACADEMIC_ADMIN))]
)
def get_detection_benchmark(
    force: bool = Query(False, description="Bypass cache and force full benchmark recalculation"),
    db: Session = Depends(get_db)
):
    """Runs decoupled evaluation comparing operational exceptions table against the isolated ground truth."""
    version = get_dataset_version()
    if version.get("status") == "GENERATING":
        raise HTTPException(
            status_code=409,
            detail="Dataset generation is currently in progress. Evaluation benchmark is temporarily unavailable."
        )
    if version.get("status") == "FAILED":
        raise HTTPException(
            status_code=500,
            detail=f"Database is in an invalid state due to previous generation failure: {version.get('error')}. Please trigger data generation again."
        )

    gen_id = version.get("generation_id") or get_dataset_fingerprint()
    if not force and gen_id:
        cached = get_cached_json(BENCHMARK_CACHE_PATH, gen_id)
        if cached is not None:
            return cached

    if db.execute(text("SELECT COUNT(*) FROM exceptions")).scalar() == 0:
        scan_and_register_anomalies(db)
    scorecard = evaluate_detection_benchmark(db)
    if gen_id:
        set_cached_json(BENCHMARK_CACHE_PATH, gen_id, scorecard)
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
