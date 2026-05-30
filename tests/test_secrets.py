"""Secret store: round-trip, file perms, tamper detection."""

from __future__ import annotations

import os
import stat

import pytest
from cryptography.exceptions import InvalidTag

from clg.core.secrets.store import SecretStore


def test_roundtrip_and_list():
    store = SecretStore()
    store.set_key("anthropic", "sk-test-123")
    assert store.get_key("anthropic") == "sk-test-123"
    assert store.list_keys() == ["anthropic"]


def test_files_are_owner_only():
    store = SecretStore()
    store.set_key("openai", "sk-abc")
    for path in (store._settings.master_key_path, store._settings.keys_path):
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o600


def test_delete():
    store = SecretStore()
    store.set_key("gemini", "k")
    store.delete_key("gemini")
    assert store.get_key("gemini") is None


def test_tampering_is_detected():
    store = SecretStore()
    store.set_key("openai", "sk-secret")
    raw = bytearray(store._settings.keys_path.read_bytes())
    raw[-1] ^= 0x01
    store._settings.keys_path.write_bytes(bytes(raw))
    with pytest.raises(InvalidTag):
        store.get_key("openai")
