from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm import LLMError, LLMService

router = APIRouter()


def get_llm_service(request: Request) -> LLMService:
    """LLM-сервис с общим httpx-клиентом из состояния приложения."""
    return LLMService(get_settings(), request.app.state.http_client)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, llm: LLMService = Depends(get_llm_service)) -> ChatResponse:
    if not get_settings().openrouter_api_key:
        raise HTTPException(status_code=503, detail="LLM не настроен: заполните OPENROUTER_API_KEY в .env")

    try:
        text, parts = await llm.ask(request.message, request.history)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return ChatResponse(text=text, parts=parts)
