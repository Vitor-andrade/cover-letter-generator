"""Anthropic (Claude) provider — pay-per-use, bring-your-own-key."""

from __future__ import annotations

from clg.core.providers.base import (
    CompletionParams,
    LLMProvider,
    ProviderError,
    ProviderHealth,
)


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def complete(self, prompt: str, params: CompletionParams) -> str:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self._api_key)
            message = client.messages.create(
                model=params.model,
                max_tokens=params.max_tokens,
                temperature=params.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            parts = [block.text for block in message.content if block.type == "text"]
            return "".join(parts).strip()
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            raise ProviderError(f"Anthropic request failed: {exc}") from exc

    def health(self) -> ProviderHealth:
        if not self._api_key:
            return ProviderHealth(available=False, detail="No Anthropic API key configured")
        return ProviderHealth(available=True, detail="Anthropic API key configured")
