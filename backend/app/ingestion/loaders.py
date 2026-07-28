"""
File loader router supporting PDF, DOCX, XLSX, TXT, and MD files.

Returns a list of LangChain Document objects.
"""

import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    TextLoader,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".md", ".png", ".jpg", ".jpeg"}


def load_file(file_path: str) -> list:
    """Route a file to the appropriate document loader. Returns list of Documents."""
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".pdf":
            return PyPDFLoader(file_path).load()
        elif ext == ".docx":
            return Docx2txtLoader(file_path).load()
        elif ext == ".xlsx":
            return UnstructuredExcelLoader(file_path, mode="elements").load()
        elif ext in (".txt", ".md"):
            return TextLoader(file_path, encoding="utf-8").load()
        elif ext in (".png", ".jpg", ".jpeg"):
            return []  # Raw standalone images are handled by image_extraction pipeline directly
        else:
            logger.warning(f"Unsupported file extension: {ext}")
            return []
    except Exception as e:
        logger.error(f"Failed to load file {file_path}: {e}")
        return []
