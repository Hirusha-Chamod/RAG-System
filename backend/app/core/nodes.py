"""
The 5 Graph Nodes for the RAG StateGraph workflow:

1. manage_history_node — summarizes older turns if history > SUMMARY_TRIGGER
2. retrieve_node — queries ChromaDB (user_id filter) & fetches parents from SQLite
3. decide_node — evaluates top cosine score against RELEVANCE_THRESHOLD (0.40)
4. synthesize_node — async LLM call with retrieved parent context
5. fallback_node — deterministic response if relevance < 0.40 (FR-10, zero hallucination)

CRITICAL LANGGRAPH RULE:
Nodes MUST return partial dicts of updated fields ONLY. Never return full state.
"""

from langchain_core.messages import SystemMessage
from app.ingestion.vectorstore import get_vectorstore
from app.ingestion.parent_store import get_parents
from app.core.llm import call_openrouter, call_openrouter_summary
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


# ── Node 1: Manage conversation history length ──────────────────────

async def manage_history_node(state):
    """Compress older conversation turns into a summary when history exceeds SUMMARY_TRIGGER."""
    messages = state.get("messages", [])
    if len(messages) <= settings.SUMMARY_TRIGGER:
        return {}  # No change needed, return empty partial dict

    older = messages[:-settings.KEEP_RECENT]
    recent = messages[-settings.KEEP_RECENT:]

    summary_text = await call_openrouter_summary(older)
    logger.info(f"Summarized {len(older)} old conversation turns into summary")

    return {
        "messages": [
            SystemMessage(content=f"Earlier conversation summary:\n{summary_text}"),
            *recent,
        ]
    }


# ── Node 2: Retrieve relevant documents ─────────────────────────────

def retrieve_node(state):
    """Query ChromaDB with user_id metadata filter, then fetch parent page text from SQLite."""
    user_id = state.get("user_id")
    query = state.get("query", "")
    vs = get_vectorstore()

    # Similarity search with cosine relevance scores and user_id filter
    results = vs.similarity_search_with_relevance_scores(
        query,
        k=settings.RETRIEVAL_K,
        filter={"user_id": user_id} if user_id else None,
    )

    if not results:
        logger.info(f"No documents retrieved for query: '{query[:40]}...' (user: {user_id})")
        return {"retrieved_docs": []}

    # Deduplicate by parent_id, retaining highest score per parent
    best_by_parent = {}
    for doc, score in results:
        pid = doc.metadata.get("parent_id")
        if pid is None:
            # Standalone image description or unparented chunk
            doc_key = f"raw_{hash(doc.page_content)}"
            best_by_parent[doc_key] = {
                "content": doc.page_content,
                "score": score,
                "source": doc.metadata.get("source", "unknown"),
                "is_raw": True,
            }
            continue

        if pid not in best_by_parent or score > best_by_parent[pid]["score"]:
            best_by_parent[pid] = {
                "score": score,
                "source": doc.metadata.get("source", "unknown"),
                "is_raw": False,
            }

    # Fetch parent (full block) text from SQLite parent store
    text_parent_ids = [pid for pid, info in best_by_parent.items() if not info["is_raw"]]
    parents = get_parents(text_parent_ids) if text_parent_ids else {}

    # Build final retrieved docs list
    retrieved_docs = []
    for pid, info in best_by_parent.items():
        if info["is_raw"]:
            retrieved_docs.append({
                "content": info["content"],
                "score": info["score"],
                "source": info["source"],
            })
        elif pid in parents:
            retrieved_docs.append({
                "content": parents[pid],
                "score": info["score"],
                "source": info["source"],
            })

    logger.info(f"Retrieved {len(retrieved_docs)} docs for query '{query[:30]}...' (scores: {[round(d['score'], 4) for d in retrieved_docs]})")
    return {"retrieved_docs": retrieved_docs}


# ── Node 3: Decide relevance (Decision Gate) ─────────────────────────

def decide_node(state):
    """Evaluate if top retrieved cosine score meets RELEVANCE_THRESHOLD."""
    docs = state.get("retrieved_docs", [])
    if not docs:
        return {"relevance_ok": False}

    top_score = max(d["score"] for d in docs)
    is_relevant = top_score >= settings.RELEVANCE_THRESHOLD

    logger.info(f"Decide gate: top_score={top_score:.4f}, threshold={settings.RELEVANCE_THRESHOLD}, relevance_ok={is_relevant}")
    return {"relevance_ok": is_relevant}


# ── Node 4: Synthesize answer from context ──────────────────────────

async def synthesize_node(state):
    """Async call to OpenRouter with retrieved parent text to generate grounded response."""
    docs = state.get("retrieved_docs", [])
    context = "\n\n---\n\n".join(
        f"[Source: {d['source']}]\n{d['content']}"
        for d in docs
    )

    answer = await call_openrouter(
        query=state["query"],
        context=context,
        history=state.get("messages", []),
        model=state.get("model"),
    )
    return {"answer": answer}


# ── Node 5: Deterministic Fallback (FR-10) ───────────────────────────

def fallback_node(state):
    """Deterministic, helpful response when relevance score is too low — zero hallucination risk."""
    return {
        "answer": (
            "I don't have any relevant documents in your library to answer that question. "
            "You can upload PDF, DOCX, XLSX, TXT, or Markdown files via the "
            "/ingest endpoint to add knowledge I can search against."
        )
    }
