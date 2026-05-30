"""API: end-to-end happy path and edge cases via the test client.

The TestClient is used as a context manager so the lifespan (schema init) runs.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from clg.api.app import create_app


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_full_flow(client):
    p = client.post(
        "/api/profiles",
        json={"name": "Vitor", "background_text": "10y backend", "source": "manual"},
    ).json()
    j = client.post(
        "/api/jobs",
        json={"title": "Staff Engineer", "company": "Acme", "description": "platform"},
    ).json()
    client.put("/api/settings", json={"ai_provider": "fake", "default_language": "en"})

    letter = client.post(
        "/api/generation",
        json={"profile_id": p["id"], "job_id": j["id"], "language": "pt", "provider": "fake"},
    ).json()
    assert letter["language"] == "pt"
    assert letter["latest_version"]["version_no"] == 1

    rev = client.post(
        "/api/generation/regenerate",
        json={"letter_id": letter["id"], "instruction": "shorter"},
    ).json()
    assert rev["version_no"] == 2

    for fmt in ("txt", "markdown", "html", "docx"):
        assert client.get(f"/api/export/{letter['id']}/{fmt}").status_code == 200


def test_provider_key_never_leaks(client):
    client.put("/api/settings/keys", json={"provider": "anthropic", "api_key": "sk-secret"})
    body = client.get("/api/settings").json()
    assert "anthropic" in body["providers_with_keys"]
    assert "sk-secret" not in json.dumps(body)


def test_missing_profile_404(client):
    assert client.get("/api/profiles/999").status_code == 404


def test_generate_missing_entities_404(client):
    resp = client.post(
        "/api/generation",
        json={"profile_id": 1, "job_id": 1, "language": "en", "provider": "fake"},
    )
    assert resp.status_code == 404
