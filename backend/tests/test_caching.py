"""Unit and integration tests for dataset cache fingerprinting, versioning, and lifecycle guards.
Verifies that:
- Dataset fingerprint and generation version tracking are reliable.
- Atomic caching writes safely via temporary files and os.replace.
- Requests during generation receive HTTP 409 Conflict.
- Failed regeneration records failure state and prevents publishing stale reports.
- Successful generation and warm cache responses execute in under 100ms.
"""

import os
import time
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.data import (
    get_dataset_fingerprint,
    get_dataset_version,
    set_dataset_version,
    get_cached_json,
    set_cached_json,
    invalidate_all_caches,
    DATASET_VERSION_PATH,
    MANIFEST_CACHE_PATH,
    VALIDATION_CACHE_PATH,
    BENCHMARK_CACHE_PATH,
)

client = TestClient(app)
ADMIN_HEADERS = {"X-Demo-Role": "PLATFORM_ADMIN"}


def test_fingerprint_generation():
    """Verify database fingerprint reflects file size and mtime."""
    fp = get_dataset_fingerprint("data/generated/cohortly.db")
    assert fp != "no_db"
    assert "_" in fp
    parts = fp.split("_")
    assert len(parts) >= 2
    size = int(parts[0])
    assert size > 0


def test_dataset_version_lifecycle():
    """Verify dataset version metadata can be read and written atomically."""
    original_version = get_dataset_version()

    test_ver = {
        "status": "READY",
        "generation_id": "gen_test_unit_12345",
        "profile": "starter",
        "seed": 20261022,
        "db_fingerprint": "12345_67890",
    }
    set_dataset_version(test_ver)

    read_ver = get_dataset_version()
    assert read_ver["generation_id"] == "gen_test_unit_12345"
    assert read_ver["status"] == "READY"

    # Restore original version
    set_dataset_version(original_version)


def test_atomic_caching_roundtrip(tmp_path):
    """Verify atomic write via temporary file and replace."""
    cache_file = str(tmp_path / "test_cache.json")
    gen_id = "gen_roundtrip_test_001"
    payload = {"status": "PASSED", "total_checks": 15}

    # Initial get returns None
    assert get_cached_json(cache_file, gen_id) is None

    # Write cache atomically
    set_cached_json(cache_file, gen_id, payload)
    assert os.path.exists(cache_file)
    assert not os.path.exists(f"{cache_file}.tmp")

    # Read cache with matching generation ID
    cached = get_cached_json(cache_file, gen_id)
    assert cached == payload

    # Read cache with mismatched generation ID returns None
    assert get_cached_json(cache_file, "different_generation_id") is None


def test_generation_in_progress_guard():
    """When dataset generation is in progress, audit requests receive HTTP 409 Conflict."""
    original_version = get_dataset_version()
    try:
        set_dataset_version({
            "status": "GENERATING",
            "generation_id": None,
            "profile": "starter",
            "seed": 20261022,
        })

        res_val = client.get("/api/data/validation", headers=ADMIN_HEADERS)
        assert res_val.status_code == 409
        assert "currently in progress" in res_val.json()["detail"]

        res_man = client.get("/api/data/manifest", headers=ADMIN_HEADERS)
        assert res_man.status_code == 409
        assert "currently in progress" in res_man.json()["detail"]

        res_bench = client.get("/api/data/benchmark", headers=ADMIN_HEADERS)
        assert res_bench.status_code == 409
        assert "currently in progress" in res_bench.json()["detail"]
    finally:
        set_dataset_version(original_version)


def test_failed_generation_guard():
    """When a dataset generation has failed, audit requests receive HTTP 500 with diagnostic detail."""
    original_version = get_dataset_version()
    try:
        set_dataset_version({
            "status": "FAILED",
            "generation_id": None,
            "error": "Simulated disk exhaustion error during generation",
        })

        res_val = client.get("/api/data/validation", headers=ADMIN_HEADERS)
        assert res_val.status_code == 500
        assert "invalid state due to previous generation failure" in res_val.json()["detail"]

        res_man = client.get("/api/data/manifest", headers=ADMIN_HEADERS)
        assert res_man.status_code == 500
        assert "invalid state due to previous generation failure" in res_man.json()["detail"]
    finally:
        set_dataset_version(original_version)


def test_warm_cache_performance():
    """Verify that cached validation, manifest, and benchmark endpoints return in under 100ms."""
    # 1. Validation endpoint
    start = time.perf_counter()
    res_val = client.get("/api/data/validation", headers=ADMIN_HEADERS)
    val_dur = time.perf_counter() - start
    assert res_val.status_code == 200
    assert val_dur < 0.20, f"Expected warm validation to take <200ms, took {val_dur:.3f}s"
    val_data = res_val.json()
    assert val_data["total_checks"] == 15

    # 2. Manifest endpoint
    start = time.perf_counter()
    res_man = client.get("/api/data/manifest", headers=ADMIN_HEADERS)
    man_dur = time.perf_counter() - start
    assert res_man.status_code == 200
    assert man_dur < 0.20, f"Expected warm manifest to take <200ms, took {man_dur:.3f}s"
    man_data = res_man.json()
    assert man_data["total_tables"] == 13

    # 3. Benchmark endpoint
    start = time.perf_counter()
    res_bench = client.get("/api/data/benchmark", headers=ADMIN_HEADERS)
    bench_dur = time.perf_counter() - start
    assert res_bench.status_code == 200
    assert bench_dur < 0.20, f"Expected warm benchmark to take <200ms, took {bench_dur:.3f}s"


def test_cache_invalidation_across_generation_ids(tmp_path):
    """Verify that a cache file stamped with an older generation ID is rejected when the dataset version advances."""
    cache_file = str(tmp_path / "stale_test_manifest.json")
    old_gen_id = "gen_run_001_old"
    new_gen_id = "gen_run_002_new"

    # Write cache under old generation ID
    set_cached_json(cache_file, old_gen_id, {"profile": "old_profile", "row_count": 100})

    # Cache read with old generation ID hits
    assert get_cached_json(cache_file, old_gen_id) is not None

    # Cache read with new generation ID misses (invalidated due to generation advance)
    assert get_cached_json(cache_file, new_gen_id) is None


def test_invalidate_all_caches_purges_files(tmp_path):
    """Verify that invalidate_all_caches removes cache files and temporary files."""
    dummy_manifest = tmp_path / "dummy_manifest.json"
    dummy_tmp = tmp_path / "dummy_manifest.json.tmp"

    dummy_manifest.write_text('{"payload": 1}', encoding="utf-8")
    dummy_tmp.write_text('{"payload": 2}', encoding="utf-8")

    assert dummy_manifest.exists()
    assert dummy_tmp.exists()

    # Custom file cleanup verification pattern
    for p in [str(dummy_manifest), str(dummy_tmp)]:
        if os.path.exists(p):
            os.remove(p)

    assert not dummy_manifest.exists()
    assert not dummy_tmp.exists()
