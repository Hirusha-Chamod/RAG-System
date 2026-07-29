"""
POST /retrieve endpoint — raw vector retrieval for authenticated users without LLM calls.

Secured with Depends(get_current_user).
"""

from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.ingestion.vectorstore import get_vectorstore
from app.ingestion.parent_store import get_parents
from app.models.schemas import RetrieveRequest, RetrieveResponse, SourceDoc
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Retrieval"])


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(
    request: RetrieveRequest,
    current_user: dict = Depends(get_current_user),
):
    """Raw vector retrieval — returns matching grounding chunks & scores without calling LLM."""
    user_id = current_user["user_id"]
    vs = get_vectorstore()

    # Query ChromaDB with cosine similarity distance and user_id filter
    results = vs.similarity_search_with_relevance_scores(
        request.query,
        k=request.k,
        filter={"user_id": user_id},
    )

    if not results:
        return RetrieveResponse(results=[], query=request.query)

    # Deduplicate by parent_id, keeping best score per parent
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

    # Fetch parent content from SQLite
    text_parent_ids = [pid for pid, info in best_by_parent.items() if not info["is_raw"]]
    parents = get_parents(text_parent_ids) if text_parent_ids else {}

    # Build response list
    source_docs = []
    for pid, info in best_by_parent.items():
        content = info["content"] if info["is_raw"] else parents.get(pid, "")
        if content:
            source_docs.append(
                SourceDoc(
                    content=content[:500],
                    score=round(info["score"], 4),
                    source=info["source"],
                )
            )

    return RetrieveResponse(results=source_docs, query=request.query)
