"""Decoupled Evaluation Benchmark Harness.
Compares independently detected exceptions in the database against the isolated ground-truth ledger.
Calculates True Positives, False Positives, False Negatives, Precision, Recall, and F1 Score.
"""

import json
import os
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models import ExceptionRecord


def evaluate_detection_benchmark(
    db: Session,
    ground_truth_path: str = "data/ground_truth/anomalies.json",
) -> Dict[str, Any]:
    """Runs evaluation benchmark comparing operational detections to ground truth."""
    if not os.path.exists(ground_truth_path):
        return {
            "error": "Ground truth file not found. Generate synthetic data first.",
            "metrics": {},
        }

    with open(ground_truth_path, "r", encoding="utf-8") as f:
        ground_truth_list = json.load(f)

    # Fetch operational detections from exceptions table
    detected_exceptions = db.query(ExceptionRecord).all()

    # Map ground truth by affected record ID
    gt_map = {item["affected_record_id"]: item for item in ground_truth_list}
    detected_map = {exc.entity_id: exc for exc in detected_exceptions}

    # Aggregate by issue type
    issue_types = ["DUPLICATE_ACTIVITY_EVENT", "UNENROLLED_LEARNER_ACTIVITY", "PREMATURE_COMPLETION", "TIMEZONE_DATE_MISMATCH"]
    type_metrics = {}

    for itype in issue_types:
        gt_ids = {k for k, v in gt_map.items() if v["issue_type"] == itype}
        det_ids = {k for k, v in detected_map.items() if v.issue_type == itype}

        tp = len(gt_ids.intersection(det_ids))
        fp = len(det_ids - gt_ids)
        fn = len(gt_ids - det_ids)

        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        f1 = round(2 * (precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0

        type_metrics[itype] = {
            "ground_truth_count": len(gt_ids),
            "detected_count": len(det_ids),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
        }

    # Total aggregate
    all_gt_ids = set(gt_map.keys())
    all_det_ids = set(detected_map.keys())

    total_tp = len(all_gt_ids.intersection(all_det_ids))
    total_fp = len(all_det_ids - all_gt_ids)
    total_fn = len(all_gt_ids - all_det_ids)

    total_precision = round(total_tp / (total_tp + total_fp), 4) if (total_tp + total_fp) > 0 else 0.0
    total_recall = round(total_tp / (total_tp + total_fn), 4) if (total_tp + total_fn) > 0 else 0.0
    total_f1 = round(2 * (total_precision * total_recall) / (total_precision + total_recall), 4) if (total_precision + total_recall) > 0 else 0.0

    return {
        "timestamp": os.path.getmtime(ground_truth_path),
        "total_ground_truth": len(all_gt_ids),
        "total_detected": len(all_det_ids),
        "aggregate": {
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn,
            "precision": total_precision,
            "recall": total_recall,
            "f1_score": total_f1,
        },
        "by_anomaly_type": type_metrics,
    }
