"""
POST /chat endpoint — executes full RAG graph workflow for authenticated users.

Secured with Depends(get_current_user).
"""

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from app.api.deps import get_graph, get_current_user
from app.models.schemas import ChatRequest, ChatResponse, SourceDoc
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    graph=Depends(get_graph),
):
    """Send a chat message to the RAG engine.
    
    Executes: manage_history -> retrieve -> decide -> synthesize / fallback.
    Maintains session history keyed by session_id (thread_id).
    """
    user_id = current_user["user_id"]
    model = request.model or settings.DEFAULT_MODEL

    # Validate model selection against server whitelist
    if model not in settings.ALLOWED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model '{model}'. Choose from: {list(settings.ALLOWED_MODELS.keys())}",
        )

    # Initial input state for the graph run
    input_state = {
        "messages": [HumanMessage(content=request.message)],
        "user_id": user_id,
        "thread_id": request.session_id,
        "query": request.message,
        "retrieved_docs": [],
        "relevance_ok": False,
        "answer": "",
        "model": model,
    }

    # Config for LangGraph checkpointing and LangSmith metadata
    config = {
        "configurable": {"thread_id": request.session_id},
        "tags": [f"user:{user_id}", f"model:{model}"],
        "metadata": {"user_id": user_id, "session_id": request.session_id, "model": model},
    }

    # Execute async graph run
    result = await graph.ainvoke(input_state, config=config)

    # Format source document citations
    sources = [
        SourceDoc(
            content=d["content"][:300],
            score=round(d["score"], 4),
            source=d["source"],
        )
        for d in result.get("retrieved_docs", [])
    ]

    return ChatResponse(
        answer=result.get("answer", ""),
        sources=sources,
        session_id=request.session_id,
        relevance_ok=result.get("relevance_ok", False),
        model_used=model,
    )
