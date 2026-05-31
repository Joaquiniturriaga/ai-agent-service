from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from src.config.settings import settings
from src.agent.fire_agent import run_agent

router = APIRouter(tags=["agent"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    response: str
    success: bool = True


def _validate_key(key: Optional[str]):
    if not key or key != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, x_internal_key: Optional[str] = Header(None)):
    _validate_key(x_internal_key)
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    history = [{"role": m.role, "content": m.content} for m in body.history]
    response = await run_agent(body.message, history)
    return ChatResponse(response=response)