"""Settings endpoints — active provider and default language.

Non-secret settings (active provider, default language) persist in the DB
``Setting`` table, overriding env defaults. Provider API keys are configured via
env (``CLG_<PROVIDER>_API_KEY``) and are never accepted or returned over the API
— only the list of providers that have a key configured is exposed.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from clg.api.deps import get_session
from clg.api.schemas import SettingsRead, SettingsUpdate
from clg.core.config import get_settings
from clg.core.persistence.repositories import SqlSettingsRepository
from clg.core.providers.registry import available_providers, cloud_providers

router = APIRouter(prefix="/api/settings", tags=["settings"])

_PROVIDER_KEY = "ai_provider"
_LANGUAGE_KEY = "default_language"


def _read(session: Session) -> SettingsRead:
    repo = SqlSettingsRepository(session)
    env = get_settings()
    return SettingsRead(
        ai_provider=repo.get(_PROVIDER_KEY) or env.ai_provider,
        default_language=repo.get(_LANGUAGE_KEY) or env.default_language,
        available_providers=available_providers(),
        providers_with_keys=[p for p in cloud_providers() if env.provider_api_key(p)],
    )


@router.get("", response_model=SettingsRead)
def get_settings_view(session: Session = Depends(get_session)) -> SettingsRead:
    return _read(session)


@router.put("", response_model=SettingsRead)
def update_settings(
    payload: SettingsUpdate, session: Session = Depends(get_session)
) -> SettingsRead:
    repo = SqlSettingsRepository(session)
    if payload.ai_provider is not None:
        repo.set(_PROVIDER_KEY, payload.ai_provider.lower())
    if payload.default_language is not None:
        repo.set(_LANGUAGE_KEY, payload.default_language)
    return _read(session)
