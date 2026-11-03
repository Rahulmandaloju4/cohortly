"""Tests for Ground-Truth Decoupling and Strict Operational Isolation.
Verifies that:
1. Operational service code and API routers NEVER import, query, or reference the ground-truth ledger.
2. The ground-truth file is isolated in data/ground_truth/anomalies.json with proper schema.
3. The benchmark evaluation module evaluates precision/recall/F1 without operational leakage.
"""

import os
import json
import pytest
from backend.app.core.database import SessionLocal
from backend.app.eval.benchmark import evaluate_detection_benchmark


def test_operational_code_zero_ground_truth_leakage():
    """Verify that operational services and routers never import or reference ground truth files."""
    operational_directories = [
        "backend/app/services",
        "backend/app/validators",
        "backend/app/models",
        "backend/app/core",
        "backend/app/utils",
    ]

    forbidden_patterns = [
        "data/ground_truth",
        "ground_truth/anomalies.json",
        "anomalies.json",
    ]

    scanned_files = []
    violations = []

    for directory in operational_directories:
        full_dir = os.path.abspath(directory)
        if not os.path.exists(full_dir):
            continue
        for root, _, files in os.walk(full_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    scanned_files.append(file_path)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        for pattern in forbidden_patterns:
                            if pattern in content:
                                violations.append(f"{file_path} contains forbidden pattern '{pattern}'")

    assert len(scanned_files) >= 5, f"Expected to scan at least 5 operational files, found {len(scanned_files)}"
    assert len(violations) == 0, f"Ground-truth leakage detected in operational code: {violations}"


def test_ground_truth_file_structure_and_schema():
    """Verify schema and validity of the isolated ground-truth ledger."""
    gt_path = "data/ground_truth/anomalies.json"
    assert os.path.exists(gt_path), "Ground truth file data/ground_truth/anomalies.json does not exist."

    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    assert isinstance(ground_truth, list)
    assert len(ground_truth) > 0

    required_keys = {"anomaly_id", "issue_type", "affected_record_id", "expected_detection", "ground_truth_label", "description"}
    for entry in ground_truth:
        missing = required_keys - set(entry.keys())
        assert not missing, f"Ground truth entry missing keys {missing}: {entry}"
        assert entry["issue_type"] in [
            "DUPLICATE_ACTIVITY_EVENT",
            "UNENROLLED_LEARNER_ACTIVITY",
            "PREMATURE_COMPLETION",
            "TIMEZONE_DATE_MISMATCH",
        ]


def test_benchmark_evaluation_on_starter_database():
    """Verify decoupled benchmark calculates precision, recall, and F1 on starter dataset."""
    db = SessionLocal()
    try:
        from backend.app.services.anomaly_detector import scan_and_register_anomalies
        # Run detection scan
        scan_and_register_anomalies(db)

        report = evaluate_detection_benchmark(db)
        agg = report["aggregate"]
        # Ground truth has 8 anomalies injected; detector should detect all 8 true positives
        assert agg["true_positives"] >= 8
        assert agg["recall"] >= 0.9  # Should have near-perfect or perfect recall
        assert agg["precision"] >= 0.8 # High precision

        for itype, m in report["by_anomaly_type"].items():
            assert m["ground_truth_count"] >= 1
            assert m["true_positives"] >= 1
    finally:
        db.close()
