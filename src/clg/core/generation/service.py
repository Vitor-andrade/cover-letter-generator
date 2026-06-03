"""Generation orchestration.

Ties together profile + job + provider to produce a cover letter and persist it
as a :class:`CoverLetter` with an initial AI :class:`LetterVersion`. Revisions
append further versions, preserving full history.

The service depends on repository Protocols and the provider abstraction, never
on concrete SQLite or SDK classes — so it is unit-testable with the fake
provider and any repository implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

from clg.core.config import Settings, get_settings
from clg.core.generation.prompt import (
    build_generation_prompt,
    build_regeneration_prompt,
)
from clg.core.persistence.models import CoverLetter, LetterVersion, VersionOrigin
from clg.core.persistence.repositories import (
    JobRepository,
    LetterRepository,
    ProfileRepository,
)
from clg.core.providers.base import CompletionParams, LLMProvider
from clg.core.providers.registry import build_provider, resolve_model


class GenerationError(RuntimeError):
    """Raised when generation cannot proceed (missing profile/job/letter)."""


@dataclass(frozen=True)
class GenerationResult:
    letter: CoverLetter
    version: LetterVersion


class GenerationService:
    def __init__(
        self,
        *,
        profiles: ProfileRepository,
        jobs: JobRepository,
        letters: LetterRepository,
        provider: LLMProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._profiles = profiles
        self._jobs = jobs
        self._letters = letters
        self._provider_override = provider
        self._settings = settings or get_settings()

    def _provider_for(self, name: str | None) -> LLMProvider:
        if self._provider_override is not None:
            return self._provider_override
        return build_provider(name, settings=self._settings)

    def generate(
        self,
        *,
        profile_id: int,
        job_id: int,
        language: str = "en",
        provider: str | None = None,
        model: str | None = None,
    ) -> GenerationResult:
        prof = self._profiles.get(profile_id)
        if prof is None:
            raise GenerationError(f"Profile {profile_id} not found")
        job = self._jobs.get(job_id)
        if job is None:
            raise GenerationError(f"Job {job_id} not found")

        provider_name = (provider or self._settings.ai_provider).lower()
        llm = self._provider_for(provider_name)
        chosen_model = resolve_model(provider_name, model)

        prompt = build_generation_prompt(
            background_text=prof.background_text,
            job_title=job.title,
            company=job.company,
            job_description=job.description,
            language=language,
            candidate_name=prof.name,
        )
        content = llm.complete(prompt, CompletionParams(model=chosen_model, language=language))
        letter = self._letters.add(
            CoverLetter(
                profile_id=profile_id,
                job_id=job_id,
                language=language,
                provider=provider_name,
                model=chosen_model,
            )
        )
        assert letter.id is not None
        version = self._letters.add_version(
            LetterVersion(
                cover_letter_id=letter.id,
                version_no=self._letters.next_version_no(letter.id),
                content=content,
                origin=VersionOrigin.ai,
            )
        )
        return GenerationResult(letter=letter, version=version)

    def regenerate_section(
        self,
        *,
        letter_id: int,
        instruction: str,
        language: str | None = None,
    ) -> LetterVersion:
        """Revise the latest version of a letter and append a new AI version."""
        letter = self._letters.get(letter_id)
        if letter is None:
            raise GenerationError(f"Cover letter {letter_id} not found")
        history = self._letters.versions(letter_id)
        if not history:
            raise GenerationError(f"Cover letter {letter_id} has no versions to revise")

        lang = language or letter.language
        llm = self._provider_for(letter.provider)
        prompt = build_regeneration_prompt(
            current_letter=history[-1].content,
            instruction=instruction,
            language=lang,
        )
        model = letter.model or resolve_model(letter.provider)
        content = llm.complete(prompt, CompletionParams(model=model, language=lang))
        return self._letters.add_version(
            LetterVersion(
                cover_letter_id=letter_id,
                version_no=self._letters.next_version_no(letter_id),
                content=content,
                origin=VersionOrigin.ai,
            )
        )
