"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

TEST_API_KEY = "test-secret"
AUTH_HEADERS = {"Authorization": f"Bearer {TEST_API_KEY}"}


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(create_app(), raise_server_exceptions=True)
