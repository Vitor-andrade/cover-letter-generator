"""Entry point for ``clg`` / ``uvx clg``.

Boots a uvicorn server bound to localhost on a free port and opens the default
browser at the app URL.
"""

from __future__ import annotations

import socket
import threading
import webbrowser

import uvicorn

from clg.api.app import create_app
from clg.core.config import get_settings


def _pick_free_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def main() -> None:
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
