"""
POST /chat, POST /chat/stream, GET /chat/history & GET /chat/sessions endpoints.
Executes full RAG graph workflow, supports real-time SSE token streaming, and persists chat history.

Secured with Depends(get_current_user).
"""

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage
from app.api.deps import get_graph, get_current_user
from app.models.schemas import ChatRequest, ChatResponse, SourceDoc
from app.core.nodes import (
    classify_query_node,
    manage_history_node,
    retrieve_node,
    decide_node,
    EXTRACTION_TRIGGER_EVERY_N_TURNS,
    FALLBACK_RESPONSE,
    GREETING_PATTERNS,
)
from app.core.llm import stream_openrouter, call_openrouter_extract_memory
from app.memory.long_term import set_memory
from app.memory.chat_history_db import (
    save_chat_message,
    get_chat_history,
    get_user_sessions,
    get_user_sessions_with_titles,
    delete_session,
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
    """Send a chat message to the 3-way RAG engine (non-streaming) and persist in SQLite history."""
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
        "query_type": "rag",
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


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """Real-time SSE token-by-token streaming endpoint powered by LangChain ChatOpenAI & LangGraph nodes."""
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

    # Fetch prior chat history messages for conversational context
    prior = get_chat_history(user_id, request.session_id)
    history_messages = []
    for msg in prior[:-1]:
        if msg["sender"] == "user":
            history_messages.append(HumanMessage(content=msg["text"]))
        elif msg["sender"] == "assistant" and msg["text"]:
            history_messages.append(AIMessage(content=msg["text"]))

    state = {
        "messages": history_messages + [HumanMessage(content=request.message)],
        "user_id": user_id,
        "thread_id": request.session_id,
        "query": request.message,
        "query_type": "rag",
        "retrieved_docs": [],
        "relevance_action": "fallback",
        "answer": "",
        "model": model,
    }

    # 2. Run graph preparation nodes
    hist_updates = await manage_history_node(state)
    state.update(hist_updates)

    classify_updates = classify_query_node(state)
    state.update(classify_updates)

    query_type = state.get("query_type", "rag")
    if query_type == "greeting":
        # Skip retrieval and reranking entirely for greetings
        state["relevance_action"] = "synthesize"
    else:
        ret_updates = retrieve_node(state)
        state.update(ret_updates)

        dec_updates = decide_node(state)
        state.update(dec_updates)

    action = state.get("relevance_action", "fallback")
    docs = state.get("retrieved_docs", [])

    sources = [
        SourceDoc(
            content=d["content"][:300],
            score=round(d.get("rerank_score", d.get("score", 0.0)), 4),
            source=d["source"],
        )
        for d in docs
    ]
    sources_dict_list = [s.model_dump() for s in sources]

    async def event_generator():
        full_response = []

        if action == "fallback":
            yield f"data: {json.dumps({'token': FALLBACK_RESPONSE})}\n\n"
            full_response.append(FALLBACK_RESPONSE)
        elif action == "clarify":
            partial_snippets = "\n".join(f"- {d['source']}: {d['content'][:150]}..." for d in docs[:3])
            clarify_prompt = f"The user query partially matched some documents, but evidence is ambiguous. Ask a brief clarifying question.\nSnippets:\n{partial_snippets}\nQuery: {request.message}"
            async for token in stream_openrouter(query=clarify_prompt, context="", history=[], model=model):
                yield f"data: {json.dumps({'token': token})}\n\n"
                full_response.append(token)
        else: # action == "synthesize"
            if query_type == "greeting" or GREETING_PATTERNS.match(request.message.strip()):
                context = "The user is saying hello, introducing themselves, or asking for assistance. Respond warmly and introduce yourself as AI Nexus RAG Engine assistant."
            else:
                context = "\n\n---\n\n".join(f"[Source: {d['source']}]\n{d['content']}" for d in docs)
            async for token in stream_openrouter(query=request.message, context=context, history=state.get("messages", []), model=model):
                yield f"data: {json.dumps({'token': token})}\n\n"
                full_response.append(token)

        complete_text = "".join(full_response)

        # Save assistant message to SQLite
        save_chat_message(
            user_id=user_id,
            session_id=request.session_id,
            sender="assistant",
            text=complete_text,
            sources=sources_dict_list,
            relevance_action=action,
            model_used=model,
        )

        # Yield metadata event line
        meta_event = {
            "type": "metadata",
            "sources": sources_dict_list,
            "relevance_action": action,
            "session_id": request.session_id,
            "model_used": model,
        }
        yield f"data: {json.dumps(meta_event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
    """Retrieve all distinct sessions with titles for the authenticated user."""
    user_id = current_user["user_id"]
    sessions_list = get_user_sessions_with_titles(user_id)
    return {"user_id": user_id, "sessions": sessions_list}


@router.delete("/sessions")
async def delete_session_endpoint(
    session_id: str = Query(..., description="Session ID to delete"),
    current_user: dict = Depends(get_current_user),
):
    """Delete a chat session and all its messages for the authenticated user."""
    user_id = current_user["user_id"]
    deleted_count = delete_session(user_id, session_id)
    return {
        "user_id": user_id,
        "session_id": session_id,
        "status": "deleted",
        "deleted_messages": deleted_count,
    }


