"""Entry point for ``clg`` / ``uvx clg``.

Boots a uvicorn server bound to localhost on a free port and opens the default
browser at the app URL.

On macOS it first makes Homebrew's native libraries discoverable so PDF export
(WeasyPrint → cairo/pango) works out of the box: the system/``uv``-managed
Python does not search ``/opt/homebrew/lib`` (or ``/usr/local/lib`` on Intel),
and dyld only reads ``DYLD_*`` at launch — so we set the path and re-exec once,
guarded by a sentinel env var to make any loop impossible.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import webbrowser
from collections.abc import Mapping, Sequence

import uvicorn

from clg.api.app import create_app
from clg.core.config import get_settings

_REEXEC_FLAG = "CLG_DYLD_REEXEC"
_DYLD_VAR = "DYLD_FALLBACK_LIBRARY_PATH"
# Homebrew lib dirs: Apple Silicon first, then Intel.
_HOMEBREW_LIB_DIRS = ("/opt/homebrew/lib", "/usr/local/lib")


def _pick_free_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _dyld_fallback_update(
    *, platform: str, env: Mapping[str, str], lib_dirs: Sequence[str]
) -> str | None:
    """Compute the new ``DYLD_FALLBACK_LIBRARY_PATH``, or ``None`` if unchanged.

    Pure (no I/O, no exec) so the decision is unit-testable. Returns a value only
    on macOS, when we have not already re-exec'd, and when at least one Homebrew
    lib dir is missing from the current fallback path.
    """
    if platform != "darwin" or env.get(_REEXEC_FLAG):
        return None
    if not lib_dirs:
        return None
    current = env.get(_DYLD_VAR, "")
    parts = current.split(os.pathsep) if current else []
    missing = [d for d in lib_dirs if d not in parts]
    if not missing:
        return None
    return os.pathsep.join([*parts, *missing])


def _ensure_macos_native_libs() -> None:
    """Make Homebrew libs visible to dyld for WeasyPrint, re-exec'ing once."""
    lib_dirs = [d for d in _HOMEBREW_LIB_DIRS if os.path.isdir(d)]
    new_value = _dyld_fallback_update(platform=sys.platform, env=os.environ, lib_dirs=lib_dirs)
    if new_value is None:
        return
    os.environ[_DYLD_VAR] = new_value
    os.environ[_REEXEC_FLAG] = "1"  # sentinel: the re-exec'd process won't loop
    os.execv(sys.executable, [sys.executable, *sys.argv])


def main() -> None:
    _ensure_macos_native_libs()

    settings = get_settings()
    settings.ensure_data_dir()

    host = settings.host
    port = settings.port or _pick_free_port(host)
    url = f"http://{host}:{port}"

    if settings.open_browser:
        # Open the browser shortly after the server starts accepting connections.
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    print(f"Cover Letter Generator running at {url}")
    uvicorn.run(create_app(), host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
