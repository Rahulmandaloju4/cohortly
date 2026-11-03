"""Integration tests for deterministic synthetic data generator."""
import pytest
import sqlite3
import os
import json
from backend.app.generators.generate import generate_dataset


@pytest.fixture(scope="module")
def starter_dataset():
    """Generates a small test dataset in a temporary sqlite database."""
    test_db_path = "data/generated/test_cohortly.db"
    summary = generate_dataset(
        profile="starter",
        seed=20261022,
        num_learners=50,
        num_courses=5,
        num_enrollments=100,
        num_events=500,
        db_path=test_db_path,
        quiet=True,
    )
    yield test_db_path, summary
    # Clean up safely on Windows
    import gc
    gc.collect()
    try:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    except OSError:
        pass


def test_starter_generation_counts(starter_dataset):
    """Verify that all entities are generated with expected record counts."""
    test_db_path, summary = starter_dataset
    counts = summary["counts"]
    
    assert counts["learners"] == 50
    assert counts["courses"] == 5
    assert counts["enrollments"] == 100
    assert counts["activity_events"] >= 500
    assert counts["content_items"] > 0
    assert counts["assessments"] > 0
    assert counts["attempts"] > 0
    assert counts["completion_rules"] == 5
    assert counts["course_outcomes"] >= 100
    assert counts["state_history"] >= 100
    assert counts["anomalies_injected"] > 0


def test_ground_truth_file_isolation(starter_dataset):
    """Verify that data/ground_truth/anomalies.json exists and contains labelled edge cases."""
    gt_path = "data/ground_truth/anomalies.json"
    assert os.path.exists(gt_path)
    with open(gt_path, "r", encoding="utf-8") as f:
        anomalies = json.load(f)
    
    assert len(anomalies) > 0
    issue_types = {a["issue_type"] for a in anomalies}
    assert "DUPLICATE_ACTIVITY_EVENT" in issue_types
    assert "UNENROLLED_LEARNER_ACTIVITY" in issue_types
    assert "PREMATURE_COMPLETION" in issue_types
    assert "TIMEZONE_DATE_MISMATCH" in issue_types


def test_database_foreign_key_integrity(starter_dataset):
    """Verify that foreign keys in the generated database are intact."""
    test_db_path, _ = starter_dataset
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_key_check;")
    violations = cursor.fetchall()
    conn.close()
    
    # Notice: Unenrolled event has enrollment_id = NULL, which is allowed by nullable foreign key.
    # Therefore, foreign_key_check should report 0 foreign key constraint violations!
    assert len(violations) == 0, f"Foreign key violations found: {violations}"
