"""Compose: structured sections render into a deterministic labeled document."""

from __future__ import annotations

from clg.core.profile.compose import compose_background_text

FULL = {
    "contact": {
        "email": "ada@example.com",
        "phone": "+44 20 7946 0000",
        "linkedin": "https://linkedin.com/in/ada",
        "location": "London, UK",
        "website": "",
    },
    "summary": "Backend engineer with 12 years building payment systems.",
    "key_skills": ["Go", "Python", "Kubernetes"],
    "skills": ["Postgres", "gRPC", "Terraform"],
    "experiences": [
        {
            "role": "Staff Engineer",
            "company": "Acme",
            "period": "2020–now",
            "location": "Remote",
            "highlights": ["Shipped payments platform at 2M req/day", "Led a team of 6"],
        }
    ],
    "projects": [
        {
            "name": "Ledger",
            "description": "Double-entry accounting lib",
            "tech": ["Go"],
            "highlights": ["10k stars"],
            "link": "https://github.com/ada/ledger",
        }
    ],
    "education": [
        {"degree": "MSc Computer Science", "institution": "UCL", "period": "2010", "details": ""}
    ],
    "certifications": [{"name": "CKA", "issuer": "CNCF", "year": "2022"}],
    "languages": [{"language": "English", "proficiency": "Native"}],
}


def test_compose_full_sections():
    out = compose_background_text(FULL)
    # Labeled sections in stable order.
    assert "## Contact" in out and "## Summary" in out and "## Experience" in out
    assert out.index("## Contact") < out.index("## Summary") < out.index("## Experience")
    # Contact joined by ' · ' (matches the prompt's expected separator).
    assert "Email: ada@example.com · Phone: +44 20 7946 0000 · LinkedIn:" in out
    # Empty website subfield omitted.
    assert "Website:" not in out
    # Experience entry composed with title/period/location + bullet highlights.
    assert "- Staff Engineer at Acme (2020–now) — Remote" in out
    assert "  - Led a team of 6" in out
    # Project link + tech.
    assert "[https://github.com/ada/ledger]" in out
    assert "  Tech: Go" in out
    # Skills CSV.
    assert "Go, Python, Kubernetes" in out


def test_compose_omits_empty_sections_and_none():
    assert compose_background_text(None) == ""
    assert compose_background_text({}) == ""
    partial = {"summary": "Just a summary.", "skills": [], "experiences": []}
    out = compose_background_text(partial)
    assert out == "## Summary\nJust a summary."
    assert "## Skills" not in out and "## Experience" not in out
