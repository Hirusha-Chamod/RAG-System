"""
ChromaDB client setup configured with cosine similarity distance metric (`hnsw:space`: `cosine`).

Uses a module-level singleton to avoid re-initializing the Chroma client on every call.
"""

from langchain_chroma import Chroma
from app.ingestion.embeddings import get_embedding_function
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_vectorstore = None


def get_vectorstore(collection_name: str = "ai_nexus_docs"):
    """Get singleton Chroma persistent vector store instance with cosine similarity space."""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=get_embedding_function(),
            persist_directory=settings.CHROMA_DB_PATH,
            collection_metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB vectorstore initialized (collection: {collection_name})")
    return _vectorstore
