"""
POST /chat & GET /chat/history endpoints — executes full RAG graph workflow and persists chat history.

Secured with Depends(get_current_user).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from langchain_core.messages import HumanMessage
from app.api.deps import get_graph, get_current_user
from app.models.schemas import ChatRequest, ChatResponse, SourceDoc
from app.memory.chat_history_db import (
    save_chat_message,
    get_chat_history,
    get_user_sessions,
)
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    graph=Depends(get_graph),
):
    """Send a chat message to the 3-way RAG engine and persist in SQLite history."""
    user_id = current_user["user_id"]
    model = request.model or settings.DEFAULT_MODEL

    if model not in settings.ALLOWED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model '{model}'. Choose from: {list(settings.ALLOWED_MODELS.keys())}",
        )

    # 1. Save user message to persistent SQLite database
    save_chat_message(
        user_id=user_id,
        session_id=request.session_id,
        sender="user",
        text=request.message,
    )

    # 2. Invoke LangGraph workflow
    input_state = {
        "messages": [HumanMessage(content=request.message)],
        "user_id": user_id,
        "thread_id": request.session_id,
        "query": request.message,
        "retrieved_docs": [],
        "relevance_action": "fallback",
        "answer": "",
        "model": model,
    }

    config = {
        "configurable": {"thread_id": request.session_id},
        "tags": [f"user:{user_id}", f"model:{model}"],
        "metadata": {"user_id": user_id, "session_id": request.session_id, "model": model},
    }

    result = await graph.ainvoke(input_state, config=config)

    sources = [
        SourceDoc(
            content=d["content"][:300],
            score=round(d.get("rerank_score", d.get("score", 0.0)), 4),
            source=d["source"],
        )
        for d in result.get("retrieved_docs", [])
    ]

    action = result.get("relevance_action", "fallback")
    answer = result.get("answer", "")

    # 3. Save assistant message to persistent SQLite database
    sources_dict_list = [s.model_dump() for s in sources]
    save_chat_message(
        user_id=user_id,
        session_id=request.session_id,
        sender="assistant",
        text=answer,
        sources=sources_dict_list,
        relevance_action=action,
        model_used=model,
    )

    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=request.session_id,
        relevance_ok=(action == "synthesize"),
        relevance_action=action,
        model_used=model,
    )


@router.get("/history")
async def get_history(
    session_id: str = Query("session_default", description="Session ID to fetch messages for"),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve persisted chat history for a specific session."""
    user_id = current_user["user_id"]
    messages = get_chat_history(user_id, session_id)
    return {"user_id": user_id, "session_id": session_id, "messages": messages}


@router.get("/sessions")
async def get_sessions(current_user: dict = Depends(get_current_user)):
    """Retrieve all distinct session IDs for the authenticated user."""
    user_id = current_user["user_id"]
    sessions = get_user_sessions(user_id)
    if "session_default" not in sessions:
        sessions.append("session_default")
    return {"user_id": user_id, "sessions": sessions}
