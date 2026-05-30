"""Encrypted local secret store for provider API keys (ADR-005).

Keys are encrypted with AES-256-GCM (authenticated encryption). A 256-bit master
key is auto-generated on first use and stored in ``~/.clg/master.key``; the
encrypted secrets blob lives in ``~/.clg/keys.bin``. Both files are created with
owner-only (``0600``) permissions. Plaintext keys exist only in memory, only when
a cloud provider call is made, and are never logged.

On-disk format of ``keys.bin`` per record (concatenated, length-prefixed):
    name_len (1 byte) | name (utf-8) | nonce (12 bytes) | ct_len (4 bytes, BE) | ciphertext

The whole file is rewritten on every mutation — fine for the handful of keys a
single user holds.
"""

from __future__ import annotations

import os
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from clg.core.config import Settings, get_settings

_KEY_BYTES = 32  # AES-256
_NONCE_BYTES = 12  # GCM standard nonce


class SecretStore:
    """Reads/writes AES-256-GCM-encrypted provider API keys on the local disk."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    # --- master key -------------------------------------------------------
    def _load_master_key(self) -> bytes:
        self._settings.ensure_data_dir()
        path = self._settings.master_key_path
        if path.exists():
            return path.read_bytes()
        key = AESGCM.generate_key(bit_length=256)
        # Write with 0600 from the start (avoid a readable window).
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(key)
        os.chmod(path, 0o600)
        return key

    def _aead(self) -> AESGCM:
        return AESGCM(self._load_master_key())

    # --- raw blob (de)serialization --------------------------------------
    def _read_records(self) -> dict[str, tuple[bytes, bytes]]:
        """Return {name: (nonce, ciphertext)} from keys.bin (empty if absent)."""
        path = self._settings.keys_path
        if not path.exists():
            return {}
        raw = path.read_bytes()
        records: dict[str, tuple[bytes, bytes]] = {}
        offset = 0
        while offset < len(raw):
            name_len = raw[offset]
            offset += 1
            name = raw[offset : offset + name_len].decode("utf-8")
            offset += name_len
            nonce = raw[offset : offset + _NONCE_BYTES]
            offset += _NONCE_BYTES
            (ct_len,) = struct.unpack_from(">I", raw, offset)
            offset += 4
            ciphertext = raw[offset : offset + ct_len]
            offset += ct_len
            records[name] = (nonce, ciphertext)
        return records

    def _write_records(self, records: dict[str, tuple[bytes, bytes]]) -> None:
        path = self._settings.keys_path
        self._settings.ensure_data_dir()
        chunks: list[bytes] = []
        for name, (nonce, ciphertext) in records.items():
            name_bytes = name.encode("utf-8")
            chunks.append(bytes([len(name_bytes)]))
            chunks.append(name_bytes)
            chunks.append(nonce)
            chunks.append(struct.pack(">I", len(ciphertext)))
            chunks.append(ciphertext)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(b"".join(chunks))
        os.chmod(path, 0o600)

    # --- public API -------------------------------------------------------
    def set_key(self, name: str, api_key: str) -> None:
        """Encrypt and persist ``api_key`` under ``name`` (e.g. a provider name)."""
        nonce = os.urandom(_NONCE_BYTES)
        # Authenticate the record name as associated data to bind ct to its slot.
        ciphertext = self._aead().encrypt(nonce, api_key.encode("utf-8"), name.encode("utf-8"))
        records = self._read_records()
        records[name] = (nonce, ciphertext)
        self._write_records(records)

    def get_key(self, name: str) -> str | None:
        """Decrypt and return the key for ``name``, or ``None`` if absent."""
        record = self._read_records().get(name)
        if record is None:
            return None
        nonce, ciphertext = record
        plaintext = self._aead().decrypt(nonce, ciphertext, name.encode("utf-8"))
        return plaintext.decode("utf-8")

    def delete_key(self, name: str) -> None:
        records = self._read_records()
        if name in records:
            del records[name]
            self._write_records(records)

    def list_keys(self) -> list[str]:
        """Return the names that have a stored key (never the secret values)."""
        return list(self._read_records().keys())
