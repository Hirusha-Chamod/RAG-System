"""
Embedding function manager supporting local sentence-transformers model (all-MiniLM-L6-v2)
or remote HuggingFace Inference API model.
"""

from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpointEmbeddings
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_embedding_function = None


def get_embedding_function():
    """Get or create singleton embedding function."""
    global _embedding_function
    if _embedding_function is not None:
        return _embedding_function

    if settings.EMBEDDING_MODE == "remote":
        logger.info(f"Initializing remote HuggingFace embeddings: {settings.EMBEDDING_MODEL}")
        _embedding_function = HuggingFaceEndpointEmbeddings(
            model=settings.EMBEDDING_MODEL,
            huggingfacehub_api_token=settings.HF_API_TOKEN,
        )
    else:
        logger.info(f"Initializing local HuggingFace embeddings: {settings.EMBEDDING_MODEL}")
        _embedding_function = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL
        )

    return _embedding_function
