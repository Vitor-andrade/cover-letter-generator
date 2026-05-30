"""FastAPI application factory.

Serves the JSON API plus the built React UI from a single localhost process.
Routers are thin adapters over the domain core; the core is never imported with
web types leaking back into it.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from clg import __version__
from clg.api.routers import export, generation, jobs, profiles, settings
from clg.core.config import get_settings
from clg.core.persistence.db import init_db

STATIC_DIR = Path(__file__).parent / "static"

# Hard cap on request body size (covers the 10 MiB upload limit plus overhead).
MAX_BODY_BYTES = 12 * 1024 * 1024


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    cfg = get_settings()
    app = FastAPI(title="Cover Letter Generator", version=__version__, lifespan=_lifespan)

    # Local-only: the server binds to 127.0.0.1, so restrict CORS to the local
    # origin as defence-in-depth (no 0.0.0.0, no wildcard origins).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[f"http://{cfg.host}:{cfg.port}", "http://localhost"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _limit_body(
        request: Request, call_next: Callable[[Request], Awaitable[object]]
    ) -> object:
        length = request.headers.get("content-length")
        if length is not None and length.isdigit() and int(length) > MAX_BODY_BYTES:
            return JSONResponse(status_code=413, content={"detail": "Request body too large"})
        return await call_next(request)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    for module in (profiles, jobs, generation, export, settings):
        app.include_router(module.router)

    _mount_ui(app)
    return app


def _mount_ui(app: FastAPI) -> None:
    """Serve the built React UI if present, with SPA fallback (never over /api)."""
    index = STATIC_DIR / "index.html"
    if index.exists():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

        @app.get("/{full_path:path}")
        def spa(full_path: str) -> FileResponse:
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
