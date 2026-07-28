"""
ChromaDB client setup configured with cosine similarity distance metric (`hnsw:space`: `cosine`).
"""

from langchain_chroma import Chroma
from app.ingestion.embeddings import get_embedding_function
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def get_vectorstore(collection_name: str = "ai_nexus_docs"):
    """Get Chroma persistent vector store instance with cosine similarity space."""
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embedding_function(),
        persist_directory=settings.CHROMA_DB_PATH,
        collection_metadata={"hnsw:space": "cosine"},
    )
