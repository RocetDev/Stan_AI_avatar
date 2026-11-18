import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import chat, health
from app.core.config import get_settings

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.http_client = httpx.AsyncClient(timeout=settings.llm_timeout)
    yield
    await app.state.http_client.aclose()


app = FastAPI(title="Stan AI Avatar", lifespan=lifespan)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    """3D-просмотрщик с ИИ-ассистентом."""
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@app.get("/ar")
async def ar_page() -> FileResponse:
    """AR-режим (требует камеру; при её отсутствии — дружелюбный fallback)."""
    return FileResponse(STATIC_DIR / "ar.html", media_type="text/html")


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
