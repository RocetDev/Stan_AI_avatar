from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "llm_configured": bool(settings.openrouter_api_key),
        "model": settings.model_name,
    }
