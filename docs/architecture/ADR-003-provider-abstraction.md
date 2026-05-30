# ADR-003: Pluggable AI provider abstraction

- **Status:** Accepted
- **Date:** 2026-05-30
- **Deciders:** Vitor (tech lead)

## Context

CLG must support a free local default (Ollama) and optional bring-your-own-key
cloud providers (Gemini, Anthropic, OpenAI), mirroring the
`linkedin-post-executor` pattern. The generation logic must not care which
backend produces text.

## Decision

Define a single `LLMProvider` interface (Python `Protocol` + ABC) with
concrete implementations `ollama`, `gemini`, `anthropic`, `openai`, selected at
runtime by configuration. Interface surface (initial):

```
class LLMProvider(Protocol):
    name: str
    def complete(self, prompt: str, *, model: str, language: str,
                 max_tokens: int, temperature: float) -> str: ...
    def stream(self, prompt: str, **kw) -> Iterator[str]: ...   # Phase B
    def health(self) -> ProviderHealth: ...
```

Selection via env: `CLG_AI_PROVIDER`, `CLG_<PROVIDER>_API_KEY`,
`CLG_<PROVIDER>_MODEL` (overridable in the Settings UI). Ollama is the default;
Gemini's free tier is the recommended free cloud fallback; Anthropic/OpenAI are
pay-per-use.

## Rationale

- Proven pattern from the sister project; consistent env convention (`CLG_`).
- Keeps `generation` decoupled — adding a provider is one new class +
  registry entry, no changes to orchestration.

## Consequences

- **Positive:** Easy provider extension; testable via a fake provider;
  uniform config story.
- **Negative:** Lowest-common-denominator interface; provider-specific features
  (tool use, JSON mode) need capability flags. Acceptable for letter
  generation.

## Alternatives considered

- **LangChain / LiteLLM wrapper:** extra dependency and abstraction weight for
  four well-documented SDKs. Rejected for v1; revisit only if provider count
  grows substantially.
