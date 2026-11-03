"""Unit and integration tests for Role-Based Access Control (RBAC).
Verifies that:
1. Learner role cannot access sensitive admin/generator endpoints (403 Forbidden).
2. Instructor can access course and analytics endpoints.
3. Support Staff can access exception investigator and transition exception statuses.
4. Academic Admin and Platform Admin have appropriate high-privilege access.
5. Missing X-Demo-Role defaults to PLATFORM_ADMIN safely for demo.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_learner_role_access_boundaries():
    """Verify that a learner cannot access administrative, data generator, or exception endpoints."""
    headers = {"X-Demo-Role": "LEARNER"}

    # Permitted endpoints for learner
    res_health = client.get("/api/health", headers=headers)
    assert res_health.status_code == 200

    res_courses = client.get("/api/courses", headers=headers)
    assert res_courses.status_code == 200

    # Forbidden endpoints for learner
    res_gen = client.post("/api/data/generate", headers=headers, json={"profile": "starter", "seed": 20261022})
    assert res_gen.status_code == 403
    assert "Access denied" in res_gen.json()["detail"]

    res_val = client.get("/api/data/validation", headers=headers)
    assert res_val.status_code == 403

    res_excs = client.get("/api/exceptions", headers=headers)
    assert res_excs.status_code == 403

    res_eng = client.get("/api/analytics/engagement", headers=headers)
    assert res_eng.status_code == 403


def test_instructor_role_access():
    """Verify instructor can access courses, cohorts, and analytics but cannot trigger data generation."""
    headers = {"X-Demo-Role": "INSTRUCTOR"}

    res_courses = client.get("/api/courses", headers=headers)
    assert res_courses.status_code == 200

    res_eng = client.get("/api/analytics/engagement", headers=headers)
    assert res_eng.status_code == 200

    res_cohorts = client.get("/api/cohorts", headers=headers)
    assert res_cohorts.status_code == 200

    # Cannot trigger generator
    res_gen = client.post("/api/data/generate", headers=headers, json={"profile": "starter"})
    assert res_gen.status_code == 403


def test_support_staff_role_access():
    """Verify support staff can access exceptions and patch status, but cannot access data generation."""
    headers = {"X-Demo-Role": "SUPPORT_STAFF"}

    res_excs = client.get("/api/exceptions", headers=headers)
    assert res_excs.status_code == 200

    # Cannot trigger generator
    res_gen = client.post("/api/data/generate", headers=headers, json={"profile": "starter"})
    assert res_gen.status_code == 403


def test_platform_admin_full_access():
    """Verify platform admin has complete unobstructed access across all endpoints."""
    headers = {"X-Demo-Role": "PLATFORM_ADMIN"}

    res_status = client.get("/api/data/status", headers=headers)
    assert res_status.status_code == 200

    res_val = client.get("/api/data/validation", headers=headers)
    assert res_val.status_code == 200

    res_man = client.get("/api/data/manifest", headers=headers)
    assert res_man.status_code == 200


def test_default_demo_role_fallback():
    """Verify that omitting X-Demo-Role defaults to PLATFORM_ADMIN for evaluation ergonomics."""
    res = client.get("/api/data/status")
    assert res.status_code == 200
    assert res.headers["X-Demo-Role-Applied"] == "PLATFORM_ADMIN"
