"""Sectionizer: local heuristic bucketing of CV text (no LLM, ADR-004)."""

from __future__ import annotations

from clg.core.ingestion.sectionize import sectionize

CV = """Ada Lovelace
Senior Backend Engineer
ada@example.com · +44 20 7946 0000
linkedin.com/in/ada

Summary
Backend engineer with 12 years building payment systems.

Skills
Go, Python, Kubernetes, Postgres

Experience
Staff Engineer at Acme (2020-now)
Led a team of 6 engineers
Shipped a payments platform at 2M req/day

Senior Engineer at Globex (2016-2020)
Built the billing service

Education
MSc Computer Science, UCL (2010)

Certifications
CKA - CNCF (2022)

Languages
English: Native
Portuguese: Fluent
"""


def test_buckets_and_contact():
    sections, low = sectionize(CV)
    assert low is False  # headers were found

    assert sections["contact"]["email"] == "ada@example.com"
    assert sections["contact"]["linkedin"] == "linkedin.com/in/ada"
    assert "44" in sections["contact"]["phone"]

    assert "Backend engineer with 12 years" in sections["summary"]
    assert sections["skills"] == ["Go", "Python", "Kubernetes", "Postgres"]

    assert sections["languages"] == [
        {"language": "English", "proficiency": "Native"},
        {"language": "Portuguese", "proficiency": "Fluent"},
    ]
    assert sections["certifications"][0]["name"] == "CKA - CNCF (2022)"
    assert sections["certifications"][0]["year"] == "2022"
    assert "MSc Computer Science" in sections["education"][0]["details"]


def test_experiences_split_into_blocks_but_subfields_left_blank():
    """The documented limitation: blocks are split, fields are NOT decomposed."""
    sections, _ = sectionize(CV)
    exps = sections["experiences"]
    assert len(exps) == 2  # two entries separated by the blank line
    # Raw lines preserved as highlights; structured subfields intentionally blank.
    assert exps[0]["role"] == "" and exps[0]["company"] == "" and exps[0]["period"] == ""
    assert "Staff Engineer at Acme (2020-now)" in exps[0]["highlights"]
    assert "Led a team of 6 engineers" in exps[0]["highlights"]
    assert "Built the billing service" in exps[1]["highlights"]


def test_no_headers_is_low_confidence():
    sections, low = sectionize("Just some freeform notes about my work and life, no headers here.")
    assert low is True
    assert "freeform notes" in sections["summary"]
    assert sections["experiences"] == []
