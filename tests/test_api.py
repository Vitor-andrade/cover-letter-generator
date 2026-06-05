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


def test_settings_reflect_env_keys(client, monkeypatch):
    from clg.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("CLG_ANTHROPIC_API_KEY", "sk-secret")
    body = client.get("/api/settings").json()
    get_settings.cache_clear()

    # The configured provider is advertised, but the key value never leaves the server.
    assert "anthropic" in body["providers_with_keys"]
    assert "sk-secret" not in json.dumps(body)


SECTIONS = {
    "contact": {"email": "ada@x.com", "location": "Berlin"},
    "summary": "Backend engineer.",
    "key_skills": ["Go", "Python"],
    "experiences": [
        {"role": "Staff", "company": "Acme", "period": "2020", "highlights": ["Led team"]}
    ],
}


def test_sections_compose_and_roundtrip(client):
    p = client.post("/api/profiles", json={"name": "Ada", "sections": SECTIONS}).json()
    # background_text is DERIVED from sections (composed markdown).
    assert "## Summary" in p["background_text"]
    assert "Backend engineer." in p["background_text"]
    assert "- Staff at Acme (2020)" in p["background_text"]
    # sections round-trip on read (missing fields default-filled).
    got = client.get(f"/api/profiles/{p['id']}").json()
    assert got["sections"]["summary"] == "Backend engineer."
    assert got["sections"]["key_skills"] == ["Go", "Python"]
    assert got["sections"]["projects"] == []


def test_patch_recomposes_background(client):
    """The dirty-tracking guard: editing sections must persist a new background_text."""
    p = client.post("/api/profiles", json={"name": "Ada", "sections": SECTIONS}).json()
    new = dict(SECTIONS, summary="Rewritten summary.")
    client.patch(f"/api/profiles/{p['id']}", json={"name": "Ada", "sections": new})
    got = client.get(f"/api/profiles/{p['id']}").json()
    assert got["sections"]["summary"] == "Rewritten summary."
    assert "Rewritten summary." in got["background_text"]


def test_legacy_unstructured_profile(client):
    p = client.post(
        "/api/profiles",
        json={"name": "Old", "background_text": "raw cv text", "source": "manual"},
    ).json()
    assert p["sections"] is None
    assert p["background_text"] == "raw cv text"


def test_missing_profile_404(client):
    assert client.get("/api/profiles/999").status_code == 404


def test_generate_missing_entities_404(client):
    resp = client.post(
        "/api/generation",
        json={"profile_id": 1, "job_id": 1, "language": "en", "provider": "fake"},
    )
    assert resp.status_code == 404
