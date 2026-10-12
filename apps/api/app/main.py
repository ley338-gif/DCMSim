from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.proxy_auth import proxy_username, reset_username, set_username
from app.db.base import Base
from app.db.session import engine

configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="DCMSim API", version="0.5.0", lifespan=lifespan)


@app.middleware("http")
async def proxy_identity(request: Request, call_next):
    username = proxy_username(request)
    if settings.proxy_auth_required and username is None:
        return JSONResponse({"detail": "Anmeldung am Reverse Proxy erforderlich"}, status_code=401)
    token = set_username(username)
    try:
        return await call_next(request)
    finally:
        reset_username(token)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

static_dir = Path(settings.static_path) if settings.static_path else Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        requested = static_dir / path
        return FileResponse(requested if requested.is_file() else static_dir / "index.html")
