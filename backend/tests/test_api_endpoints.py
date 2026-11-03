"""Contract and integration tests for all 25+ REST API endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_dashboard_endpoints():
    """Verify all dashboard overview and trend endpoints."""
    headers = {"X-Demo-Role": "PLATFORM_ADMIN"}

    res = client.get("/api/dashboard/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_learners" in data
    assert "waler" in data
    assert "waeer" in data
    assert "overall_completion_rate" in data
    assert "at_risk_learner_count" in data

    res2 = client.get("/api/dashboard/engagement-trend?weeks=4", headers=headers)
    assert res2.status_code == 200
    trend = res2.json()
    assert len(trend) == 4
    assert "waler" in trend[0]
    assert "waeer" in trend[0]

    res3 = client.get("/api/dashboard/completion-trend", headers=headers)
    assert res3.status_code == 200
    comp_trend = res3.json()
    assert len(comp_trend) > 0
    assert "completion_rate" in comp_trend[0]


def test_learners_endpoints():
    """Verify learners directory, profile with explainable outcomes, and activity timeline."""
    headers = {"X-Demo-Role": "PLATFORM_ADMIN"}

    # List
    res = client.get("/api/learners?page=1&page_size=10", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    assert len(data["items"]) <= 10
    first_id = data["items"][0]["learner_id"]

    # Detail
    res_det = client.get(f"/api/learners/{first_id}", headers=headers)
    assert res_det.status_code == 200
    det = res_det.json()
    assert det["learner_id"] == first_id
    assert "enrollments" in det
    assert "overall_risk_level" in det

    # Activity timeline
    res_act = client.get(f"/api/learners/{first_id}/activity?page=1&page_size=5", headers=headers)
    assert res_act.status_code == 200
    act = res_act.json()
    assert "items" in act


def test_courses_endpoints():
    """Verify course catalog, curriculum hierarchy tree, and drop-off analytics."""
    headers = {"X-Demo-Role": "PLATFORM_ADMIN"}

    res = client.get("/api/courses?page=1&page_size=10", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    first_cid = data["items"][0]["course_id"]

    # Course detail with nested curriculum
    res_det = client.get(f"/api/courses/{first_cid}", headers=headers)
    assert res_det.status_code == 200
    det = res_det.json()
    assert det["course_id"] == first_cid
    assert len(det["curriculum"]) > 0
    assert "children" in det["curriculum"][0]

    # Course drop-off analytics
    res_an = client.get(f"/api/courses/{first_cid}/analytics", headers=headers)
    assert res_an.status_code == 200
    an = res_an.json()
    assert "drop_off_funnel" in an
    assert "completion_rate" in an


def test_cohorts_endpoints():
    """Verify cohort listing, analytics, and multi-cohort timeline comparison."""
    headers = {"X-Demo-Role": "PLATFORM_ADMIN"}

    res = client.get("/api/cohorts", headers=headers)
    assert res.status_code == 200
    cohorts = res.json()
    assert len(cohorts) > 0
    first_coh = cohorts[0]["cohort_id"]
    second_coh = cohorts[1]["cohort_id"] if len(cohorts) > 1 else first_coh

    # Cohort analytics
    res_an = client.get(f"/api/cohorts/{first_coh}/analytics", headers=headers)
    assert res_an.status_code == 200
    an = res_an.json()
    assert "risk_distribution" in an
    assert "waler" in an

    # Multi-cohort comparison
    res_comp = client.get(f"/api/cohorts/compare?cohort_ids={first_coh}&cohort_ids={second_coh}", headers=headers)
    assert res_comp.status_code == 200
    comp = res_comp.json()
    assert len(comp["cohorts"]) >= 1
    assert "engagement_timeline" in comp["cohorts"][0]


def test_assessments_endpoints():
    """Verify assessment catalog and granular learner attempt progress."""
    headers = {"X-Demo-Role": "PLATFORM_ADMIN"}

    res = client.get("/api/assessments", headers=headers)
    assert res.status_code == 200
    asms = res.json()
    assert len(asms) > 0
    assert "pass_rate" in asms[0]

    res_prog = client.get("/api/assessments/progress?page=1&page_size=10", headers=headers)
    assert res_prog.status_code == 200
    prog = res_prog.json()
    assert "items" in prog


def test_analytics_endpoints():
    """Verify dimensional engagement, completion, and content usage breakdowns."""
    headers = {"X-Demo-Role": "PLATFORM_ADMIN"}

    res_eng = client.get("/api/analytics/engagement", headers=headers)
    assert res_eng.status_code == 200
    eng = res_eng.json()
    assert "by_region" in eng
    assert "by_device" in eng
    assert "by_learning_mode" in eng

    res_comp = client.get("/api/analytics/completion", headers=headers)
    assert res_comp.status_code == 200
    comp = res_comp.json()
    assert "by_category" in comp
    assert "by_program_type" in comp
    assert "by_difficulty" in comp

    res_usage = client.get("/api/analytics/content-usage", headers=headers)
    assert res_usage.status_code == 200
    usage = res_usage.json()
    assert len(usage) > 0
    assert "drop_off_pct" in usage[0]


def test_exceptions_endpoints():
    """Verify anomaly investigator listing, forensic detail, and state history transition."""
    headers = {"X-Demo-Role": "PLATFORM_ADMIN"}

    res = client.get("/api/exceptions?page=1&page_size=10", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    first_exc = data["items"][0]["exception_id"]

    # Forensic detail
    res_det = client.get(f"/api/exceptions/{first_exc}", headers=headers)
    assert res_det.status_code == 200
    det = res_det.json()
    assert det["exception_id"] == first_exc
    assert "evidence" in det
    assert "relevant_rule" in det

    # Update status -> INVESTIGATING
    patch_res = client.patch(
        f"/api/exceptions/{first_exc}/status",
        headers=headers,
        json={"status": "INVESTIGATING", "reason": "Triage investigation commenced by QA", "actor_id": "TESTER-01"}
    )
    assert patch_res.status_code == 200
    assert "transitioned" in patch_res.json()["message"]


def test_data_management_endpoints():
    """Verify data status, 15-point validation, SHA-256 manifest, benchmark scorecard, and streaming exports."""
    headers = {"X-Demo-Role": "PLATFORM_ADMIN"}

    # Status
    res_st = client.get("/api/data/status", headers=headers)
    assert res_st.status_code == 200
    st = res_st.json()
    assert st["total_records"] > 0
    assert len(st["tables"]) == 13

    # Validation
    res_val = client.get("/api/data/validation", headers=headers)
    assert res_val.status_code == 200
    val = res_val.json()
    assert val["total_checks"] == 15
    assert val["is_healthy"] is True

    # Manifest
    res_man = client.get("/api/data/manifest", headers=headers)
    assert res_man.status_code == 200
    man = res_man.json()
    assert len(man["tables"]) == 13
    assert len(man["tables"][0]["sha256_checksum"]) == 64

    # Benchmark
    res_bm = client.get("/api/data/benchmark", headers=headers)
    assert res_bm.status_code == 200
    bm = res_bm.json()
    assert bm["aggregate"]["true_positives"] >= 8

    # CSV Export
    res_csv = client.get("/api/data/export/csv?table=courses", headers=headers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "course_id" in res_csv.text

    # JSON Export
    res_json = client.get("/api/data/export/json?table=cohorts", headers=headers)
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers["content-type"]
    assert len(res_json.json()) > 0
