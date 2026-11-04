"""Concurrency and Stress Tests for Multi-threaded API Requests.
Verifies that:
- Concurrent requests across audit, dashboard, courses, and learner endpoints succeed without SQLite disk I/O errors or lock contention.
- Multi-threaded read operations against cached manifests and validation reports return consistent HTTP 200 responses.
"""

import concurrent.futures
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
ADMIN_HEADERS = {"X-Demo-Role": "PLATFORM_ADMIN", "X-Demo-Learner-Id": "LRN-000001"}


def fetch_endpoint(url: str, headers: dict = ADMIN_HEADERS) -> int:
    """Helper to execute single request and return status code."""
    res = client.get(url, headers=headers)
    return res.status_code


def test_concurrent_cached_audit_execution():
    """Executes 20 concurrent requests across validation, manifest, and benchmark endpoints.
    Verifies that all concurrent workers succeed without SQLite locking or disk I/O errors.
    """
    urls = [
        "/api/data/validation",
        "/api/data/manifest",
        "/api/data/benchmark",
        "/api/dashboard/overview",
        "/api/courses?page=1&page_size=5",
        "/api/learners/LRN-000001",
    ] * 4  # 24 requests in total

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_endpoint, u) for u in urls]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == len(urls)
    assert all(code == 200 for code in results), f"Expected all HTTP 200, but got: {results}"


def test_concurrent_mixed_role_requests():
    """Executes concurrent requests with mixed demo roles to verify thread safety of RBAC context."""
    requests = [
        ("/api/dashboard/overview", {"X-Demo-Role": "PLATFORM_ADMIN"}, 200),
        ("/api/dashboard/overview", {"X-Demo-Role": "LEARNER"}, 200),
        ("/api/learners", {"X-Demo-Role": "LEARNER"}, 403),
        ("/api/learners", {"X-Demo-Role": "SUPPORT_STAFF"}, 200),
        ("/api/learners/LRN-000001", {"X-Demo-Role": "LEARNER", "X-Demo-Learner-Id": "LRN-000001"}, 200),
        ("/api/learners/LRN-000002", {"X-Demo-Role": "LEARNER", "X-Demo-Learner-Id": "LRN-000001"}, 403),
        ("/api/data/validation", {"X-Demo-Role": "LEARNER"}, 403),
        ("/api/data/validation", {"X-Demo-Role": "ACADEMIC_ADMIN"}, 200),
    ] * 3

    def execute_role_req(req):
        url, headers, expected_code = req
        res = client.get(url, headers=headers)
        return res.status_code == expected_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(execute_role_req, req) for req in requests]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert all(results), "Expected all concurrent mixed-role requests to match their expected status codes."
