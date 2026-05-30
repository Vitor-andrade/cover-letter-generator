"""Google Gemini provider — recommended free cloud fallback, bring-your-own-key."""

from __future__ import annotations

from clg.core.providers.base import (
    CompletionParams,
    LLMProvider,
    ProviderError,
    ProviderHealth,
)


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def complete(self, prompt: str, params: CompletionParams) -> str:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self._api_key)
            response = client.models.generate_content(
                model=params.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=params.temperature,
                    max_output_tokens=params.max_tokens,
                ),
            )
            return (response.text or "").strip()
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            raise ProviderError(f"Gemini request failed: {exc}") from exc

    def health(self) -> ProviderHealth:
        if not self._api_key:
            return ProviderHealth(available=False, detail="No Gemini API key configured")
        return ProviderHealth(available=True, detail="Gemini API key configured")
