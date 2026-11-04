"""Authoritative Role-Based Access Control (RBAC) Matrix Verification.
Tests all operational endpoints across all 5 demo roles:
- PLATFORM_ADMIN
- ACADEMIC_ADMIN
- INSTRUCTOR
- SUPPORT_STAFF
- LEARNER

Total: 27 distinct HTTP method + endpoint operations x 5 roles = 135 test cases.
(Both GET and POST /api/cohorts/compare tested independently).
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

ALL_ROLES = [
    "PLATFORM_ADMIN",
    "ACADEMIC_ADMIN",
    "INSTRUCTOR",
    "SUPPORT_STAFF",
    "LEARNER",
]

# Canonical operational endpoints with exact HTTP methods, URLs, sample payloads, and authorized roles
OPERATIONS = [
    # 1-4: Public / All 5 Roles
    {
        "id": "health",
        "method": "GET",
        "url": "/api/health",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF", "LEARNER"],
    },
    {
        "id": "dashboard_overview",
        "method": "GET",
        "url": "/api/dashboard/overview",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF", "LEARNER"],
    },
    {
        "id": "dashboard_engagement_trend",
        "method": "GET",
        "url": "/api/dashboard/engagement-trend?weeks=6",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF", "LEARNER"],
    },
    {
        "id": "dashboard_completion_trend",
        "method": "GET",
        "url": "/api/dashboard/completion-trend",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF", "LEARNER"],
    },

    # 5-7: Courses
    {
        "id": "courses_list",
        "method": "GET",
        "url": "/api/courses?page=1&page_size=5",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF", "LEARNER"],
    },
    {
        "id": "course_detail",
        "method": "GET",
        "url": "/api/courses/CRS-000001",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF", "LEARNER"],
    },
    {
        "id": "course_analytics",
        "method": "GET",
        "url": "/api/courses/CRS-000001/analytics",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF"],
    },

    # 8-11: Cohorts
    {
        "id": "cohorts_list",
        "method": "GET",
        "url": "/api/cohorts",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF"],
    },
    {
        "id": "cohort_detail",
        "method": "GET",
        "url": "/api/cohorts/COH-2026-0001",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF"],
    },
    {
        "id": "cohort_analytics",
        "method": "GET",
        "url": "/api/cohorts/COH-2026-0001/analytics",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF"],
    },
    {
        "id": "cohorts_compare_get",
        "method": "GET",
        "url": "/api/cohorts/compare?cohort_ids=COH-2026-0001&cohort_ids=COH-2026-0002",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF"],
    },
    {
        "id": "cohorts_compare_post",
        "method": "POST",
        "url": "/api/cohorts/compare",
        "payload": ["COH-2026-0001", "COH-2026-0002"],
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF"],
    },

    # 12-14: Learners
    {
        "id": "learners_list",
        "method": "GET",
        "url": "/api/learners?page=1&page_size=5",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF"],
    },
    {
        "id": "learner_detail_self",
        "method": "GET",
        "url": "/api/learners/LRN-000001",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF", "LEARNER"],
    },
    {
        "id": "learner_activity_self",
        "method": "GET",
        "url": "/api/learners/LRN-000001/activity?page_size=5",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF", "LEARNER"],
    },

    # 15-17: Analytics
    {
        "id": "analytics_engagement",
        "method": "GET",
        "url": "/api/analytics/engagement",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR"],
    },
    {
        "id": "analytics_content_usage",
        "method": "GET",
        "url": "/api/analytics/content-usage",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR"],
    },
    {
        "id": "analytics_completion",
        "method": "GET",
        "url": "/api/analytics/completion",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR"],
    },

    # 18-20: Exceptions & State Transitions
    {
        "id": "exceptions_list",
        "method": "GET",
        "url": "/api/exceptions?page=1&page_size=5",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF"],
    },
    {
        "id": "exception_detail",
        "method": "GET",
        "url": "/api/exceptions/EXC-000001",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF"],
    },
    {
        "id": "exception_status_update",
        "method": "PATCH",
        "url": "/api/exceptions/EXC-000001/status",
        "payload": {
            "status": "INVESTIGATING",
            "reason": "Automated RBAC matrix test transition verification",
            "actor_id": "TEST-ACTOR",
        },
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN", "INSTRUCTOR", "SUPPORT_STAFF"],
    },

    # 21-26: Data Management, Audit, Benchmark & Exports
    {
        "id": "data_status",
        "method": "GET",
        "url": "/api/data/status",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN"],
    },
    {
        "id": "data_validation",
        "method": "GET",
        "url": "/api/data/validation",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN"],
    },
    {
        "id": "data_manifest",
        "method": "GET",
        "url": "/api/data/manifest",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN"],
    },
    {
        "id": "data_benchmark",
        "method": "GET",
        "url": "/api/data/benchmark",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN"],
    },
    {
        "id": "data_export",
        "method": "GET",
        "url": "/api/data/export/csv?table=learners",
        "payload": None,
        "allowed_roles": ["PLATFORM_ADMIN", "ACADEMIC_ADMIN"],
    },
    {
        "id": "data_generate",
        "method": "POST",
        "url": "/api/data/generate",
        "payload": {"profile": "invalid_probe_profile_for_rbac_test"},
        "allowed_roles": ["PLATFORM_ADMIN"],
    },
]


@pytest.mark.parametrize("role", ALL_ROLES)
@pytest.mark.parametrize("op", OPERATIONS, ids=lambda op: op["id"])
def test_rbac_matrix_endpoint(role: str, op: dict):
    """Verifies that an endpoint returns 200 (or non-403) for allowed roles,
    and returns strictly 403 Forbidden with clean detail message for restricted roles.
    For self-service learner endpoints, X-Demo-Learner-Id: LRN-000001 is provided.
    """
    headers = {
        "X-Demo-Role": role,
        "X-Demo-Learner-Id": "LRN-000001",
    }
    method = op["method"]
    url = op["url"]
    payload = op["payload"]
    is_allowed = role in op["allowed_roles"]

    if method == "GET":
        res = client.get(url, headers=headers)
    elif method == "POST":
        res = client.post(url, json=payload, headers=headers)
    elif method == "PATCH":
        res = client.patch(url, json=payload, headers=headers)
    else:
        raise ValueError(f"Unsupported method {method}")

    if is_allowed:
        # Allowed role should NOT be blocked by RBAC
        assert res.status_code != 403, (
            f"Expected role '{role}' to be ALLOWED on {method} {url}, but received HTTP 403: {res.text}"
        )
        if op["id"] == "data_generate":
            # For data_generate, we passed invalid probe profile so it should fail schema validation (422),
            # proving that PLATFORM_ADMIN passed the RBAC dependency check.
            assert res.status_code == 422
        else:
            # All other endpoints should return HTTP 200 (or 404 only if target mock ID doesn't exist)
            assert res.status_code in (200, 404), (
                f"Expected HTTP 200/404 for role '{role}' on {method} {url}, got {res.status_code}: {res.text}"
            )
    else:
        # Restricted role MUST be blocked with HTTP 403 Forbidden
        assert res.status_code == 403, (
            f"Expected role '{role}' to be RESTRICTED (HTTP 403) on {method} {url}, but got {res.status_code}: {res.text}"
        )
        data = res.json()
        assert "Access denied" in data.get("detail", ""), (
            f"Expected 'Access denied' in detail for role '{role}' on {method} {url}, got: {data}"
        )
