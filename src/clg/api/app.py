"""FastAPI application factory.

Serves the JSON API plus the built React UI (when present) from a single
process. The app binds to localhost only; CORS is restricted to the local
origin. Routers are added in later phases — this shell wires the health check
and static-file/SPA fallback so the skeleton is runnable end-to-end.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from clg import __version__
from clg.core.config import get_settings

STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Cover Letter Generator", version=__version__)

    # Local-only: the server binds to 127.0.0.1, so restrict CORS to the
    # local origin as defence-in-depth (SEC: no 0.0.0.0, no wildcard origins).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[f"http://{settings.host}:{settings.port}", "http://localhost"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    _mount_ui(app)
    return app


def _mount_ui(app: FastAPI) -> None:
    """Serve the built React UI if it exists, with SPA fallback to index.html.

    Until the UI is built (``web/`` → ``src/clg/api/static``), the root route
    returns a friendly placeholder instead of a 404.
    """
    index = STATIC_DIR / "index.html"
    if index.exists():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

        @app.get("/{full_path:path}")
        def spa(full_path: str) -> FileResponse:  # noqa: ARG001 - path captured for SPA routing
            return FileResponse(index)
    else:

        @app.get("/")
        def placeholder() -> JSONResponse:
            return JSONResponse(
                {
                    "app": "Cover Letter Generator",
                    "version": __version__,
                    "ui": "not built yet — run the UI build (web/) to populate static/",
                    "health": "/api/health",
                }
            )
