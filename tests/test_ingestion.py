"""Ingestion: manual normalization, low-confidence signal, type/size guards."""

from __future__ import annotations

import pytest

from clg.core.ingestion.parse import (
    MAX_INPUT_BYTES,
    IngestionError,
    extract_upload,
    normalize_manual,
)


def test_manual_high_confidence():
    result = normalize_manual("a" * 100)
    assert result.low_confidence is False
    assert result.source == "manual"


def test_manual_low_confidence_on_short_text():
    assert normalize_manual("short").low_confidence is True


def test_unsupported_type_rejected():
    with pytest.raises(IngestionError):
        extract_upload("resume.txt", b"hello")


def test_oversized_pdf_rejected():
    with pytest.raises(IngestionError):
        extract_upload("resume.pdf", b"x" * (MAX_INPUT_BYTES + 1))
