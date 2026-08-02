"""
POST /retrieve endpoint — raw vector retrieval for authenticated users without LLM calls.

Secured with Depends(get_current_user).
"""

from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.core.retrieval import retrieve_candidate_parents
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
    candidates = retrieve_candidate_parents(request.query, user_id=user_id, k=request.k)

    source_docs = [
        SourceDoc(
            content=c["content"][:500],
            score=round(c.get("score", 0.0), 4),
            source=c["source"],
        )
        for c in candidates
    ]

    return RetrieveResponse(results=source_docs, query=request.query)
