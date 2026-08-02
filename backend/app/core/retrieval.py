"""
Core retrieval service: Stage 1 ChromaDB vector search + parent-fetch deduplication.
"""

from app.ingestion.vectorstore import get_vectorstore
from app.ingestion.parent_store import get_parents
from app.utils.logging import get_logger

logger = get_logger(__name__)


def retrieve_candidate_parents(query: str, user_id: str | None, k: int) -> list[dict]:
    """Execute Stage 1 similarity search in ChromaDB, deduplicate by parent_id, and fetch parent texts from SQLite."""
    vs = get_vectorstore()

    results = vs.similarity_search_with_relevance_scores(
        query,
        k=k,
        filter={"user_id": user_id} if user_id else None,
    )

    if not results:
        logger.info(f"No documents retrieved for query: '{query[:40]}...' (user: {user_id})")
        return []

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

    return candidates
