"""
Local Cross-Encoder Reranker using `cross-encoder/ms-marco-MiniLM-L-2-v2`.

Performs Stage 2 re-ranking on candidate Parent documents using sentence-transformers.
Runs 100% locally on CPU (~45MB model, zero API cost).
Loaded once at server startup (lifespan) to avoid per-request thread blocking.
"""

from functools import lru_cache
from sentence_transformers import CrossEncoder
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder | None:
    """Load singleton CrossEncoder model at startup. Uses local_files_only=True for 0ms load."""
    try:
        logger.info(f"Loading cached local CrossEncoder model: {settings.RERANK_MODEL}")
        return CrossEncoder(settings.RERANK_MODEL, local_files_only=True)
    except Exception as e:
        logger.warning(f"Local CrossEncoder model load skipped ({e}). Cosine similarity active.")
        return None


def rerank_parents(query: str, parents: list[dict], top_n: int = 5) -> list[dict]:
    """Re-rank candidate Parent document dictionaries using CrossEncoder scores.
    
    Falls back gracefully to Cosine Similarity ranking if CrossEncoder is unavailable.
    Returns top_n parents sorted by rerank_score descending.
    """
    if not parents:
        return parents

    try:
        reranker = get_reranker()
        if reranker is not None:
            pairs = [(query, p["content"]) for p in parents]
            scores = reranker.predict(pairs)

            for p, s in zip(parents, scores):
                p["rerank_score"] = float(s)

            reranked = sorted(parents, key=lambda p: p["rerank_score"], reverse=True)[:top_n]
            logger.info(f"Re-ranked {len(parents)} candidate parents down to top {len(reranked)} (top score: {reranked[0]['rerank_score']:.4f})")
            return reranked
    except Exception as e:
        logger.warning(f"CrossEncoder evaluation skipped ({e}). Falling back to Cosine Similarity.")

    # Fallback: rank by Cosine similarity score
    for p in parents:
        cosine_val = p.get("score", 0.0)
        p["rerank_score"] = float(cosine_val)

    fallback_sorted = sorted(parents, key=lambda p: p["rerank_score"], reverse=True)[:top_n]
    return fallback_sorted
