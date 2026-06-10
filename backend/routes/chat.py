"""
Chat API route.

POST /api/chat
  Request body:  { "message": "...", "session_id": "..." }
  Response body: { "reply": "..." }
"""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.graph.chatbot.graph import graph

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    """Send a message to the LangGraph agent and return its reply."""
    config = {"configurable": {"thread_id": body.session_id}}

    result = await graph.ainvoke(
        {"messages": [("user", body.message)]},
        config=config,
    )

    ai_message = result["messages"][-1]
    return ChatResponse(reply=ai_message.content)
