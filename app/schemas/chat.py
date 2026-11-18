from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    text: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)

    @field_validator("history")
    @classmethod
    def limit_history(cls, v: list[ChatMessage]) -> list[ChatMessage]:
        # Берём только последние 10 реплик — длинная история не нужна
        return v[-10:]


class ChatResponse(BaseModel):
    text: str
    parts: list[str] = Field(default_factory=list)
