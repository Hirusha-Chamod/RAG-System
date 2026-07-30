"""
Local Cross-Encoder Reranker using `cross-encoder/ms-marco-MiniLM-L-6-v2`.

Performs Stage 2 re-ranking on candidate Parent documents using sentence-transformers.
Runs 100% locally on CPU (~80MB model, downloaded once).
"""

from functools import lru_cache
from sentence_transformers import CrossEncoder
from app.utils.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    """Load singleton CrossEncoder model (~80MB local model)."""
    logger.info("Initializing local CrossEncoder reranker: cross-encoder/ms-marco-MiniLM-L-6-v2")
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank_parents(query: str, parents: list[dict], top_n: int = 5) -> list[dict]:
    """Re-rank candidate Parent document dictionaries using CrossEncoder scores.
    
    Returns top_n parents sorted by rerank_score descending.
    """
    if not parents:
        return parents

    reranker = get_reranker()
    # Form (query, content) pairs for CrossEncoder joint evaluation
    pairs = [(query, p["content"]) for p in parents]
    scores = reranker.predict(pairs)

    for p, s in zip(parents, scores):
        p["rerank_score"] = float(s)

    # Sort descending by CrossEncoder logit score
    reranked = sorted(parents, key=lambda p: p["rerank_score"], reverse=True)[:top_n]
    
    logger.info(f"Re-ranked {len(parents)} candidate parents down to top {len(reranked)} (top score: {reranked[0]['rerank_score']:.4f})")
    return reranked
