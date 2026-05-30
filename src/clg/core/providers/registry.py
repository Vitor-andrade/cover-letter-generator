"""Provider registry and selection.

Maps a provider name to a builder that constructs a configured
:class:`LLMProvider`, pulling cloud API keys from the encrypted secret store
(ADR-005) and the active provider/model from settings or ``CLG_`` env vars.
"""

from __future__ import annotations

from collections.abc import Callable

from clg.core.config import Settings, get_settings
from clg.core.providers.anthropic import AnthropicProvider
from clg.core.providers.base import LLMProvider, ProviderError
from clg.core.providers.fake import FakeProvider
from clg.core.providers.gemini import GeminiProvider
from clg.core.providers.ollama import OllamaProvider
from clg.core.providers.openai import OpenAIProvider
from clg.core.secrets.store import SecretStore

# Default model per provider; overridable via CLG_<PROVIDER>_MODEL or settings.
DEFAULT_MODELS: dict[str, str] = {
    "ollama": "llama3.1",
    "gemini": "gemini-2.0-flash",
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "fake": "fake-1",
}

_CLOUD = {"gemini", "anthropic", "openai"}

ProviderBuilder = Callable[[str], LLMProvider]


def available_providers() -> list[str]:
    return ["ollama", "gemini", "anthropic", "openai"]


def _build_cloud(name: str, api_key: str) -> LLMProvider:
    if name == "gemini":
        return GeminiProvider(api_key)
    if name == "anthropic":
        return AnthropicProvider(api_key)
    if name == "openai":
        return OpenAIProvider(api_key)
    raise ProviderError(f"Unknown cloud provider: {name}")


def build_provider(
    name: str | None = None,
    *,
    settings: Settings | None = None,
    secrets: SecretStore | None = None,
) -> LLMProvider:
    """Construct the selected provider.

    Resolution order for the provider name: explicit arg → settings/env
    (``CLG_AI_PROVIDER``) → ``ollama``. Cloud providers require a stored API key.
    """
    settings = settings or get_settings()
    secrets = secrets or SecretStore(settings)
    name = (name or settings.ai_provider or "ollama").lower()

    if name == "ollama":
        return OllamaProvider()
    if name == "fake":
        return FakeProvider()
    if name in _CLOUD:
        api_key = secrets.get_key(name)
        if not api_key:
            raise ProviderError(
                f"No API key stored for provider '{name}'. Add one in Settings."
            )
        return _build_cloud(name, api_key)
    raise ProviderError(f"Unknown provider: {name}")


def resolve_model(name: str, requested: str | None = None) -> str:
    """Pick the model: explicit request → per-provider default."""
    return requested or DEFAULT_MODELS.get(name, DEFAULT_MODELS["ollama"])
