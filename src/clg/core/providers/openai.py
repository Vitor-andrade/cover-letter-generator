"""OpenAI provider — pay-per-use, bring-your-own-key."""

from __future__ import annotations

from clg.core.providers.base import (
    CompletionParams,
    LLMProvider,
    ProviderError,
    ProviderHealth,
)


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def complete(self, prompt: str, params: CompletionParams) -> str:
        try:
            import openai

            client = openai.OpenAI(api_key=self._api_key)
            completion = client.chat.completions.create(
                model=params.model,
                max_tokens=params.max_tokens,
                temperature=params.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return (completion.choices[0].message.content or "").strip()
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            raise ProviderError(f"OpenAI request failed: {exc}") from exc

    def health(self) -> ProviderHealth:
        if not self._api_key:
            return ProviderHealth(available=False, detail="No OpenAI API key configured")
        return ProviderHealth(available=True, detail="OpenAI API key configured")
