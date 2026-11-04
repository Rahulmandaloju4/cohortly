import os
import sys
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath("."))

from backend.app.core.database import SessionLocal
from backend.app.api.data import (
    get_dataset_fingerprint,
    get_dataset_version,
    set_dataset_version,
    set_cached_json,
    compute_table_manifest,
    VALIDATION_CACHE_PATH,
    MANIFEST_CACHE_PATH,
    BENCHMARK_CACHE_PATH,
)
from backend.app.validators.integrity_validator import run_15_point_validation
from backend.app.eval.benchmark import evaluate_detection_benchmark

def main():
    db = SessionLocal()
    try:
        fp = get_dataset_fingerprint("data/generated/cohortly.db")
        print(f"Operational database fingerprint: {fp}")

        gen_id = f"gen_full_20261022_{fp.split('_')[0]}"
        version_data = {
            "generation_id": gen_id,
            "profile": "full",
            "seed": 20261022,
            "status": "READY",
            "db_fingerprint": fp,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
        set_dataset_version(version_data)
        print(f"Wrote dataset version metadata: {gen_id}")

        # Validation report
        print("Pre-computing validation report...")
        val_rep = run_15_point_validation(db)
        set_cached_json(VALIDATION_CACHE_PATH, gen_id, val_rep)
        print("Validation report cached successfully.")

        # Manifest
        print("Pre-computing table manifest...")
        manifest = compute_table_manifest(db)
        manifest_dict = manifest.model_dump() if hasattr(manifest, "model_dump") else manifest.dict()
        set_cached_json(MANIFEST_CACHE_PATH, gen_id, manifest_dict)
        print("Table manifest cached successfully.")

        # Benchmark
        print("Pre-computing detection benchmark scorecard...")
        bench = evaluate_detection_benchmark(db)
        set_cached_json(BENCHMARK_CACHE_PATH, gen_id, bench)
        print("Benchmark scorecard cached successfully.")

        print("=== ALL CACHES INITIALIZED SUCCESSFULLY ===")
    finally:
        db.close()

if __name__ == "__main__":
    main()
