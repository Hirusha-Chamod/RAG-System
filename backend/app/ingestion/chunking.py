"""
Parent-child text splitting logic.

Uses RecursiveCharacterTextSplitter twice:
1. `parent_splitter` (~2000 chars) for rich context in LLM synthesis (saved in SQLite)
2. `child_splitter` (~400 chars) for precise vector embedding & search (saved in ChromaDB)
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Parent splitter: ~2000 chars
parent_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
)

# Child splitter: ~400 chars
child_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def split_into_parents_and_children(doc, file_id: str, doc_index: int = 0) -> tuple[list[dict], list[dict]]:
    """Split a loaded Document into ~2000 char parents and ~400 char children.

    Works uniformly across PDFs, DOCX, XLSX, TXT, and MD files.
    Returns (parents_list, children_list).
    """
    parent_texts = parent_splitter.split_text(doc.page_content)

    parents = []
    children = []

    for p_idx, parent_text in enumerate(parent_texts):
        parent_id = f"{file_id}_d{doc_index}_p{p_idx}"

        parents.append({
            "parent_id": parent_id,
            "content": parent_text,
            "source": doc.metadata.get("source", "unknown"),
        })

        child_texts = child_splitter.split_text(parent_text)
        for c_idx, child_text in enumerate(child_texts):
            children.append({
                "content": child_text,
                "metadata": {
                    **doc.metadata,
                    "parent_id": parent_id,
                    "chunk_index": c_idx,
                },
            })

    logger.debug(f"Doc {doc_index} split into {len(parents)} parents and {len(children)} children")
    return parents, children
