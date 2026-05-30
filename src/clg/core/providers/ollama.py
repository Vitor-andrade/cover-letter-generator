"""Ollama provider — the free, local, offline default.

Talks to a local Ollama daemon (default ``http://127.0.0.1:11434``). Requires no
API key. If the daemon is not running, :meth:`health` reports it and
:meth:`complete` raises :class:`ProviderError`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from clg.core.providers.base import (
    CompletionParams,
    LLMProvider,
    ProviderError,
    ProviderHealth,
)

if TYPE_CHECKING:
    from ollama import Client


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, host: str = "http://127.0.0.1:11434") -> None:
        self._host = host

    def _client(self) -> Client:
        import ollama

        return ollama.Client(host=self._host)

    def complete(self, prompt: str, params: CompletionParams) -> str:
        try:
            response = self._client().generate(
                model=params.model,
                prompt=prompt,
                options={
                    "temperature": params.temperature,
                    "num_predict": params.max_tokens,
                },
            )
        except Exception as exc:  # noqa: BLE001 - normalize SDK/connection errors
            raise ProviderError(f"Ollama request failed: {exc}") from exc
        return str(response.get("response", "")).strip()

    def health(self) -> ProviderHealth:
        try:
            self._client().list()
        except Exception as exc:  # noqa: BLE001 - daemon likely not running
            return ProviderHealth(available=False, detail=f"Ollama not reachable: {exc}")
        return ProviderHealth(available=True, detail=f"Ollama reachable at {self._host}")
