"""Tests for GET /api/v1/health."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def test_health_databricks_up(client: TestClient) -> None:
    with patch(
        "app.api.v1.endpoints.health.databricks_jobs.check_connectivity",
        new=AsyncMock(return_value=True),
    ):
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["dependencies"]["databricks"] == "healthy"


def test_health_databricks_down(client: TestClient) -> None:
    with patch(
        "app.api.v1.endpoints.health.databricks_jobs.check_connectivity",
        new=AsyncMock(return_value=False),
    ):
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["dependencies"]["databricks"] == "unreachable"


def test_health_returns_version_and_env(client: TestClient) -> None:
    with patch(
        "app.api.v1.endpoints.health.databricks_jobs.check_connectivity",
        new=AsyncMock(return_value=True),
    ):
        response = client.get("/api/v1/health")

    body = response.json()
    assert "version" in body
    assert "environment" in body
