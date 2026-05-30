"""LLM provider abstraction (ADR-003).

A single :class:`LLMProvider` interface with swappable implementations selected
by name. ``generation`` depends only on this interface, never on a concrete SDK,
so adding a provider is a new class + one registry entry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ProviderHealth:
    """Result of a provider readiness probe."""

    available: bool
    detail: str = ""


@dataclass(frozen=True)
class CompletionParams:
    """Tunable knobs passed to a completion call."""

    model: str
    language: str = "en"
    max_tokens: int = 1024
    temperature: float = 0.7


@runtime_checkable
class LLMProvider(Protocol):
    """The contract every provider implementation must satisfy."""

    name: str

    def complete(self, prompt: str, params: CompletionParams) -> str:
        """Return a single completion for ``prompt``."""
        ...

    def health(self) -> ProviderHealth:
        """Report whether the provider is configured and reachable."""
        ...


class ProviderError(RuntimeError):
    """Raised when a provider cannot fulfil a request (missing key, unreachable, etc.)."""
