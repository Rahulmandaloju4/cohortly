"""Basic health check and system endpoint test."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check():
    """Verify that /api/health returns HTTP 200 with expected system metadata."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["platform"] == "Cohortly"
    assert "tagline" in data
    assert "version" in data


def test_demo_role_header_applied():
    """Verify that demo role middleware inspects X-Demo-Role header."""
    response = client.get("/api/health", headers={"X-Demo-Role": "INSTRUCTOR"})
    assert response.status_code == 200
    assert response.headers.get("X-Demo-Role-Applied") == "INSTRUCTOR"
