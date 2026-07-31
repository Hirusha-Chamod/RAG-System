"""
The 6 Graph Nodes for the RAG StateGraph workflow with Long-Term Memory & Greeting Detection:

1. manage_history_node — injects long-term user memories + summarizes older turns if history > SUMMARY_TRIGGER
2. retrieve_node — Stage 1 vector search (k=15) + SQLite parent fetch + Stage 2 CrossEncoder reranking (top 5)
3. decide_node — 3-way decision gate with greeting detection (synthesize >= 0.0, clarify -2.0 to 0.0, fallback < -2.0)
4. synthesize_node — async LLM call with top re-ranked parent context + periodic memory fact extraction
5. clarify_node — async LLM call asking user for clarification on ambiguous partial matches
6. fallback_node — deterministic response if score < RERANK_CLARIFY_THRESHOLD (FR-10, zero hallucination)

CRITICAL LANGGRAPH RULE:
Nodes MUST return partial dicts of updated fields ONLY. Never return full state.
"""

import time
import re
import warnings
from langchain_core.messages import SystemMessage
from app.ingestion.vectorstore import get_vectorstore
from app.ingestion.parent_store import get_parents
from app.memory.long_term import get_all_memory, set_memory
from app.core.reranker import rerank_parents
from app.core.llm import (
    call_openrouter,
    call_openrouter_summary,
    call_openrouter_extract_memory,
)
from app.config import settings
from app.utils.logging import get_logger

# Suppress harmless ChromaDB vector relevance score float warning
warnings.filterwarnings("ignore", message="Relevance scores must be between 0 and 1")

logger = get_logger(__name__)

CLARIFY_PROMPT = (
    "You are AI Nexus assistant. The user's query partially matched some documents, "
    "but the evidence is ambiguous or incomplete to give a definitive answer.\n"
    "Look at the partially matched document snippets below and politely ask the user "
    "a clarifying question so they can refine their question."
)

EXTRACTION_TRIGGER_EVERY_N_TURNS = 5

GREETING_PATTERNS = re.compile(
    r"^\s*(hello|hi|hey|greetings|good\s+(morning|afternoon|evening)|howdy|who\s+are\s+you|what\s+can\s+you\s+do|help|my\s+name\s+is|i\s+am\s+).*",
    re.IGNORECASE,
)


# ── Node 1: Manage history & Inject Long-Term Memory ──────────────────────

async def manage_history_node(state):
    """Inject long-term user memories + compress older conversation turns if history > SUMMARY_TRIGGER."""
    user_id = state.get("user_id")
    messages = list(state.get("messages", []))
    updates = {}

    memories = get_all_memory(user_id) if user_id else {}
    if memories and not state.get("_memory_injected"):
        mem_summary = "; ".join(f"{k}: {v}" for k, v in memories.items())
        memory_sys_msg = SystemMessage(content=f"User background & context:\n{mem_summary}")
        messages.insert(0, memory_sys_msg)
        updates["_memory_injected"] = True

    if len(messages) > settings.SUMMARY_TRIGGER:
        older = messages[:-settings.KEEP_RECENT]
        recent = messages[-settings.KEEP_RECENT:]
        summary_text = await call_openrouter_summary(older)
        logger.info(f"Summarized {len(older)} old conversation turns into summary")

        updates["messages"] = [
            SystemMessage(content=f"Earlier conversation summary:\n{summary_text}"),
            *recent,
        ]
    elif updates.get("_memory_injected"):
        updates["messages"] = messages

    return updates


# ── Node 2: Two-Stage Retrieve & Re-Rank ────────────────────────────

def retrieve_node(state):
    """Stage 1: Widened ChromaDB vector search (k=15, user_id filter).
    Stage 2: Fetch parent texts from SQLite & re-rank using CrossEncoder down to top_n=5.
    """
    user_id = state.get("user_id")
    query = state.get("query", "")
    vs = get_vectorstore()

    results = vs.similarity_search_with_relevance_scores(
        query,
        k=settings.RETRIEVAL_K,
        filter={"user_id": user_id} if user_id else None,
    )

    if not results:
        logger.info(f"No documents retrieved for query: '{query[:40]}...' (user: {user_id})")
        return {"retrieved_docs": []}

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

    text_parent_ids = [pid for pid, info in best_by_parent.items() if not info["is_raw"]]
    parents = get_parents(text_parent_ids) if text_parent_ids else {}

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

    reranked_docs = rerank_parents(query, candidates, top_n=settings.TOP_N_SYNTHESIS)
    return {"retrieved_docs": reranked_docs}


# ── Node 3: 3-Way Decision Gate (with Greeting Detection) ───────────

def decide_node(state):
    """3-Way Decision Gate."""
    query = state.get("query", "").strip()

    if GREETING_PATTERNS.match(query):
        logger.info(f"Greeting detected ('{query}') -> routing to synthesize_node")
        return {"relevance_action": "synthesize"}

    docs = state.get("retrieved_docs", [])
    if not docs:
        return {"relevance_action": "fallback"}

    top_score = max(d.get("rerank_score", d.get("score", float("-inf"))) for d in docs)

    if top_score >= settings.RERANK_PASS_THRESHOLD:
        action = "synthesize"
    elif top_score >= settings.RERANK_CLARIFY_THRESHOLD:
        action = "clarify"
    else:
        action = "fallback"

    logger.info(f"3-Way Decide Gate: top_score={top_score:.4f} -> action='{action}'")
    return {"relevance_action": action}


# ── Node 4: Synthesize answer from context & Extract Memory ──────────

async def synthesize_node(state):
    """Async call to OpenRouter with top re-ranked parent text context."""
    docs = state.get("retrieved_docs", [])
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    query = state.get("query", "").strip()

    if GREETING_PATTERNS.match(query):
        context = "The user is saying hello, introducing themselves, or asking for assistance. Respond warmly and introduce yourself as AI Nexus RAG Engine assistant."
    else:
        context = "\n\n---\n\n".join(
            f"[Source: {d['source']}]\n{d['content']}"
            for d in docs
        )

    answer = await call_openrouter(
        query=state["query"],
        context=context,
        history=messages,
        model=state.get("model"),
    )

    if user_id and len(messages) > 0 and len(messages) % EXTRACTION_TRIGGER_EVERY_N_TURNS == 0:
        recent_snippet = messages[-EXTRACTION_TRIGGER_EVERY_N_TURNS:]
        extracted_fact = await call_openrouter_extract_memory(recent_snippet)
        if extracted_fact:
            set_memory(user_id, key=f"fact_{int(time.time())}", value=extracted_fact)

    return {"answer": answer}


# ── Node 5: Clarify question for ambiguous matches ───────────────────

async def clarify_node(state):
    """Async call asking user to clarify their query based on partial document matches."""
    docs = state.get("retrieved_docs", [])
    partial_snippets = "\n".join(f"- {d['source']}: {d['content'][:150]}..." for d in docs[:3])

    prompt = (
        f"{CLARIFY_PROMPT}\n\n"
        f"Partial Match Snippets:\n{partial_snippets}\n\n"
        f"User Query: {state['query']}"
    )

    answer = await call_openrouter(
        query=prompt,
        context="",
        history=[],
        model=state.get("model"),
    )
    return {"answer": answer}


# ── Node 6: Deterministic Fallback (FR-10) ───────────────────────────

def fallback_node(state):
    """Deterministic response when score is below clarify threshold — zero hallucination risk."""
    return {
        "answer": (
            "I don't have any relevant documents in your library to answer that question. "
            "You can upload PDF, DOCX, XLSX, TXT, or Markdown files via the "
            "/ingest endpoint to add knowledge I can search against."
        )
    }
