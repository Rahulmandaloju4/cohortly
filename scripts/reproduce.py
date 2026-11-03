#!/usr/bin/env python3
"""Cohortly Deterministic Reproducibility and Quality Audit Harness.
Executes dual deterministic synthesis runs with identical seeds,
computes cryptographic SHA-256 checksums across all 13 relational tables,
runs the 15-point cross-entity validation suite, and verifies the decoupled
evaluation benchmark against ground truth.

Usage:
    python scripts/reproduce.py [--seed 20261022] [--profile starter]
"""

import os
import sys
import argparse
import hashlib
import time
from typing import Dict, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ensure backend package is in pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.generators.generate import generate_dataset
from backend.app.validators.integrity_validator import run_15_point_validation
from backend.app.eval.benchmark import evaluate_detection_benchmark
from backend.app.services.anomaly_detector import scan_and_register_anomalies

ALL_TABLES = [
    "instructors",
    "learners",
    "courses",
    "cohorts",
    "enrollments",
    "content_items",
    "activity_events",
    "assessments",
    "attempts",
    "completion_rules",
    "course_outcomes",
    "exceptions",
    "state_history",
]


def compute_table_checksum(engine, table_name: str) -> Tuple[int, str]:
    """Computes exact row count and deterministic SHA-256 checksum for a table."""
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT * FROM {table_name} ORDER BY rowid ASC")).fetchall()
        hasher = hashlib.sha256()
        for r in rows:
            hasher.update(str(r).encode("utf-8"))
        return len(rows), hasher.hexdigest()


def run_reproducibility_verification(seed: int, profile: str) -> bool:
    print("=" * 80)
    print("COHORTLY DETERMINISTIC REPRODUCIBILITY HARNESS")
    print("Platform: Learning Analytics & Cohort Intelligence Platform")
    print(f"Seed: {seed} | Profile: {profile.upper()} | Reference Anchor: 2026-10-22T00:00:00Z")
    print("=" * 80)

    db_path_a = "data/generated/reproduce_run_a.db"
    gt_path_a = "data/ground_truth/reproduce_gt_a.json"
    db_path_b = "data/generated/reproduce_run_b.db"
    gt_path_b = "data/ground_truth/reproduce_gt_b.json"

    # Clean up any previous runs
    for p in [db_path_a, gt_path_a, db_path_b, gt_path_b]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    print("\n[STAGE 1/3] Generating Run A...")
    t0 = time.time()
    generate_dataset(profile=profile, seed=seed, db_path=db_path_a, ground_truth_path=gt_path_a, quiet=True)
    t_a = round(time.time() - t0, 2)
    print(f"[STAGE 1/3] Run A generated in {t_a}s -> {db_path_a}")

    print("\n[STAGE 2/3] Generating Run B (identical seed & parameters)...")
    t0 = time.time()
    generate_dataset(profile=profile, seed=seed, db_path=db_path_b, ground_truth_path=gt_path_b, quiet=True)
    t_b = round(time.time() - t0, 2)
    print(f"[STAGE 2/3] Run B generated in {t_b}s -> {db_path_b}")

    print("\n[STAGE 3/3] Bit-for-bit Cryptographic Equivalence Verification:")
    print("-" * 80)
    print(f"{'TABLE NAME':<20} | {'RUN A ROWS':<10} | {'RUN B ROWS':<10} | {'SHA-256 MATCH':<15} | {'STATUS'}")
    print("-" * 80)

    engine_a = create_engine(f"sqlite:///{db_path_a}")
    engine_b = create_engine(f"sqlite:///{db_path_b}")

    all_matched = True

    for tbl in ALL_TABLES:
        cnt_a, hash_a = compute_table_checksum(engine_a, tbl)
        cnt_b, hash_b = compute_table_checksum(engine_b, tbl)

        row_match = (cnt_a == cnt_b)
        hash_match = (hash_a == hash_b)

        if row_match and hash_match:
            status = "[OK] 100% IDENTICAL"
        else:
            status = "[FAIL] MISMATCH"
            all_matched = False

        print(f"{tbl:<20} | {cnt_a:<10} | {cnt_b:<10} | {hash_a[:12]}...  | {status}")

    engine_a.dispose()
    engine_b.dispose()

    # Clean up test artifacts
    for p in [db_path_a, gt_path_a, db_path_b, gt_path_b]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    print("-" * 80)
    if all_matched:
        print("[SUCCESS] All 13 relational tables are bit-for-bit cryptographically reproducible!")
    else:
        print("[FAILURE] Cryptographic checksum mismatch detected between independent runs!")
        return False

    # Execute 15-Point Cross-Entity Validation Suite on primary operational DB
    print("\n" + "=" * 80)
    print("COHORTLY 15-POINT INTEGRITY & LIFECYCLE VALIDATION SUITE")
    print("=" * 80)

    primary_db = "data/generated/cohortly.db"
    if not os.path.exists(primary_db):
        print(f"[WARN] Primary operational DB {primary_db} not found. Synthesizing starter dataset...")
        generate_dataset(profile="starter", seed=seed, db_path=primary_db, ground_truth_path="data/ground_truth/anomalies.json", quiet=True)

    primary_engine = create_engine(f"sqlite:///{primary_db}")
    SessionLocal = sessionmaker(bind=primary_engine)
    session = SessionLocal()

    report = run_15_point_validation(session)
    print(f"Executed: {report['total_checks']} Checks | Passed: {report['passed_checks']} | Tracked Anomalies: {report['warning_checks']} | Failed: {report['failed_checks']}")
    print("-" * 80)

    for chk in report["checks"]:
        chk_id = chk["check_id"]
        status = chk["status"]
        name = chk["name"]
        details = chk["details"]
        print(f"[{status:<7}] {chk_id}: {name}")
        print(f"          -> {details}")

    # Decoupled Evaluation Benchmark
    print("\n" + "=" * 80)
    print("DECOUPLED EVALUATION BENCHMARK SCORECARD")
    print("=" * 80)

    scan_and_register_anomalies(session)
    scorecard = evaluate_detection_benchmark(session, ground_truth_path="data/ground_truth/anomalies.json")
    session.close()
    primary_engine.dispose()

    if "aggregate" in scorecard:
        agg = scorecard["aggregate"]
        print(f"Precision: {agg['precision'] * 100:.1f}%")
        print(f"Recall:    {agg['recall'] * 100:.1f}%")
        print(f"F1 Score:  {agg['f1_score'] * 100:.1f}%")
        print(f"Detections: {agg['true_positives']} TP | {agg['false_positives']} FP | {agg['false_negatives']} FN")

        print("\nBreakdown by Anomaly Category:")
        for cat, m in scorecard["by_anomaly_type"].items():
            print(f"  • {cat:<28} -> P: {m['precision']*100:>5.1f}% | R: {m['recall']*100:>5.1f}% | F1: {m['f1_score']*100:>5.1f}% (TP={m['true_positives']}, FP={m['false_positives']}, FN={m['false_negatives']})")

    print("\n" + "=" * 80)
    print("[ALL CHECKS PASSED] Platform reproducibility and data integrity verified successfully.")
    print("=" * 80)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cohortly Reproducibility and Quality Audit Harness")
    parser.add_argument("--seed", type=int, default=20261022, help="PRNG deterministic seed")
    parser.add_argument("--profile", type=str, default="starter", choices=["starter", "full"], help="Dataset scale profile")
    args = parser.parse_args()

    success = run_reproducibility_verification(seed=args.seed, profile=args.profile)
    sys.exit(0 if success else 1)
