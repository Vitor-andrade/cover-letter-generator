"""Deterministic fake provider for tests — no network, no key."""

from __future__ import annotations

from clg.core.providers.base import CompletionParams, LLMProvider, ProviderHealth


class FakeProvider(LLMProvider):
    """Echoes a deterministic transformation of the prompt.

    Useful for asserting orchestration/persistence without hitting a real model.
    The output is stable for a given (prompt, language) pair.
    """

    name = "fake"

    def complete(self, prompt: str, params: CompletionParams) -> str:
        return f"[fake:{params.language}] {prompt[:120]}"

    def health(self) -> ProviderHealth:
        return ProviderHealth(available=True, detail="Fake provider always available")
