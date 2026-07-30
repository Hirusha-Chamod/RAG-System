"""
The 5 Graph Nodes for the RAG StateGraph workflow:

1. manage_history_node — summarizes older turns if history > SUMMARY_TRIGGER
2. retrieve_node — Stage 1 vector search (k=15) + SQLite parent fetch + Stage 2 CrossEncoder reranking (top 5)
3. decide_node — evaluates top CrossEncoder rerank_score against RERANK_THRESHOLD (-2.0)
4. synthesize_node — async LLM call with top re-ranked parent context
5. fallback_node — deterministic response if relevance < RERANK_THRESHOLD (FR-10, zero hallucination)

CRITICAL LANGGRAPH RULE:
Nodes MUST return partial dicts of updated fields ONLY. Never return full state.
"""

from langchain_core.messages import SystemMessage
from app.ingestion.vectorstore import get_vectorstore
from app.ingestion.parent_store import get_parents
from app.core.reranker import rerank_parents
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


# ── Node 2: Two-Stage Retrieve & Re-Rank ────────────────────────────

def retrieve_node(state):
    """Stage 1: Widened ChromaDB vector search (k=15, user_id filter).
    Stage 2: Fetch parent texts from SQLite & re-rank using CrossEncoder down to top_n=5.
    """
    user_id = state.get("user_id")
    query = state.get("query", "")
    vs = get_vectorstore()

    # Stage 1: Similarity search with cosine relevance scores (k=15 widened pool)
    results = vs.similarity_search_with_relevance_scores(
        query,
        k=settings.RETRIEVAL_K,
        filter={"user_id": user_id} if user_id else None,
    )

    if not results:
        logger.info(f"No documents retrieved for query: '{query[:40]}...' (user: {user_id})")
        return {"retrieved_docs": []}

    # Deduplicate candidate chunks by parent_id, keeping highest cosine score
    best_by_parent = {}
    for doc, score in results:
        pid = doc.metadata.get("parent_id")
        if pid is None:
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

    # Fetch full parent block texts from SQLite parent store
    text_parent_ids = [pid for pid, info in best_by_parent.items() if not info["is_raw"]]
    parents = get_parents(text_parent_ids) if text_parent_ids else {}

    # Assemble candidate list for CrossEncoder reranking
    candidates = []
    for pid, info in best_by_parent.items():
        if info["is_raw"]:
            candidates.append({
                "content": info["content"],
                "score": info["score"],
                "source": info["source"],
            })
        elif pid in parents:
            candidates.append({
                "content": parents[pid],
                "score": info["score"],
                "source": info["source"],
            })

    # Stage 2: Local CrossEncoder re-ranking down to top 5
    reranked_docs = rerank_parents(query, candidates, top_n=settings.TOP_N_SYNTHESIS)
    
    return {"retrieved_docs": reranked_docs}


# ── Node 3: Decide relevance (Decision Gate) ─────────────────────────

def decide_node(state):
    """Evaluate top CrossEncoder rerank_score against RERANK_THRESHOLD."""
    docs = state.get("retrieved_docs", [])
    if not docs:
        return {"relevance_ok": False}

    # Extract highest CrossEncoder score (logit scale)
    top_score = max(d.get("rerank_score", d.get("score", float("-inf"))) for d in docs)
    is_relevant = top_score >= settings.RERANK_THRESHOLD

    logger.info(f"Decide gate: top_rerank_score={top_score:.4f}, threshold={settings.RERANK_THRESHOLD}, relevance_ok={is_relevant}")
    return {"relevance_ok": is_relevant}


# ── Node 4: Synthesize answer from context ──────────────────────────

async def synthesize_node(state):
    """Async call to OpenRouter with top re-ranked parent text context."""
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
    """Deterministic response when rerank score is below threshold — zero hallucination risk."""
    return {
        "answer": (
            "I don't have any relevant documents in your library to answer that question. "
            "You can upload PDF, DOCX, XLSX, TXT, or Markdown files via the "
            "/ingest endpoint to add knowledge I can search against."
        )
    }
