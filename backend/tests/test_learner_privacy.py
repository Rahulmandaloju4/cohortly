"""Unit and integration tests for Learner Data Privacy and Ownership Enforcement.
Verifies that:
- A user with role LEARNER can only access their own profile and activity (self-service).
- Changing the learner ID in the URL returns HTTP 403 Forbidden.
- The learners directory (roster) remains strictly restricted (HTTP 403) for LEARNER.
- Staff and admin roles (PLATFORM_ADMIN, ACADEMIC_ADMIN, INSTRUCTOR, SUPPORT_STAFF) can inspect any learner.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

OWN_LEARNER_ID = "LRN-000001"
OTHER_LEARNER_ID = "LRN-000002"
STAFF_ROLES = ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF"]


def test_learner_can_access_own_profile():
    """Learner with X-Demo-Role: LEARNER and matching X-Demo-Learner-Id can access their own profile."""
    headers = {
        "X-Demo-Role": "LEARNER",
        "X-Demo-Learner-Id": OWN_LEARNER_ID,
    }
    res = client.get(f"/api/learners/{OWN_LEARNER_ID}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["learner_id"] == OWN_LEARNER_ID


def test_learner_can_access_own_activity():
    """Learner with X-Demo-Role: LEARNER and matching X-Demo-Learner-Id can access their own activity stream."""
    headers = {
        "X-Demo-Role": "LEARNER",
        "X-Demo-Learner-Id": OWN_LEARNER_ID,
    }
    res = client.get(f"/api/learners/{OWN_LEARNER_ID}/activity", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data


def test_learner_cannot_access_other_learner_profile():
    """Learner attempting to access another learner's profile receives HTTP 403 Forbidden."""
    headers = {
        "X-Demo-Role": "LEARNER",
        "X-Demo-Learner-Id": OWN_LEARNER_ID,
    }
    res = client.get(f"/api/learners/{OTHER_LEARNER_ID}", headers=headers)
    assert res.status_code == 403
    data = res.json()
    assert "Access denied" in data["detail"]
    assert "not authorized to access records of learner" in data["detail"]


def test_learner_cannot_access_other_learner_activity():
    """Learner attempting to access another learner's activity receives HTTP 403 Forbidden."""
    headers = {
        "X-Demo-Role": "LEARNER",
        "X-Demo-Learner-Id": OWN_LEARNER_ID,
    }
    res = client.get(f"/api/learners/{OTHER_LEARNER_ID}/activity", headers=headers)
    assert res.status_code == 403
    data = res.json()
    assert "Access denied" in data["detail"]


def test_url_tampering_blocked_for_learner():
    """Altering learner ID in URL path without matching credentials is strictly blocked."""
    headers = {
        "X-Demo-Role": "LEARNER",
        "X-Demo-Learner-Id": OWN_LEARNER_ID,
    }
    for malicious_id in ["LRN-000003", "LRN-000042", "LRN-999999"]:
        res = client.get(f"/api/learners/{malicious_id}", headers=headers)
        assert res.status_code == 403
        assert "Access denied" in res.json()["detail"]


def test_learners_directory_restricted_for_learner():
    """The full learners roster (/api/learners) is strictly restricted to staff and denied to LEARNER."""
    headers = {
        "X-Demo-Role": "LEARNER",
        "X-Demo-Learner-Id": OWN_LEARNER_ID,
    }
    res = client.get("/api/learners", headers=headers)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]


@pytest.mark.parametrize("role", STAFF_ROLES)
def test_staff_roles_can_inspect_any_learner_profile(role: str):
    """Staff and administrators can inspect any learner profile regardless of learner ID."""
    headers = {"X-Demo-Role": role}
    res = client.get(f"/api/learners/{OWN_LEARNER_ID}", headers=headers)
    assert res.status_code in (200, 404)
    res_other = client.get(f"/api/learners/{OTHER_LEARNER_ID}", headers=headers)
    assert res_other.status_code in (200, 404)


@pytest.mark.parametrize("role", STAFF_ROLES)
def test_staff_roles_can_inspect_any_learner_activity(role: str):
    """Staff and administrators can inspect any learner activity stream regardless of learner ID."""
    headers = {"X-Demo-Role": role}
    res = client.get(f"/api/learners/{OWN_LEARNER_ID}/activity", headers=headers)
    assert res.status_code == 200
    res_other = client.get(f"/api/learners/{OTHER_LEARNER_ID}/activity", headers=headers)
    assert res_other.status_code == 200
