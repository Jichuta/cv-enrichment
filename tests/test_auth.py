"""Tests for Bearer token authentication."""

import pytest
from fastapi.testclient import TestClient

AUTH_HEADERS = {"Authorization": "Bearer test-secret"}

# Any protected endpoint works for auth tests — use the sync enrich route
_PROTECTED = "/api/v1/cv/enrich/sync"
_PAYLOAD = {
    "jobDescription": {"title": "Engineer"},
    "greenhouseParseData": {
        "candidateId": "1",
        "firstName": "Jane",
        "lastName": "Doe",
    },
    "jsonCvTextExtracted": {},
}


def test_missing_auth_header_returns_401(client: TestClient) -> None:
    response = client.post(_PROTECTED, json=_PAYLOAD)
    assert response.status_code == 401


def test_wrong_token_returns_401(client: TestClient) -> None:
    response = client.post(
        _PROTECTED,
        json=_PAYLOAD,
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401


@pytest.mark.parametrize(
    "header",
    [
        "Basic dXNlcjpwYXNz",  # Basic auth scheme
        "Bearer",  # Missing token value
        "token-without-scheme",
    ],
)
def test_malformed_auth_header_returns_401(client: TestClient, header: str) -> None:
    response = client.post(
        _PROTECTED,
        json=_PAYLOAD,
        headers={"Authorization": header},
    )
    assert response.status_code == 401
