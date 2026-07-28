"""
Image extraction utilities for PDF, DOCX, and XLSX files.

- PDF: PyMuPDF (fitz) extracts per-page images with page numbers.
- DOCX & XLSX: ZIP extraction (word/media/, xl/media/) using standard library `zipfile`.
"""

import os
import fitz  # PyMuPDF
import zipfile
from pathlib import Path
from app.utils.logging import get_logger

logger = get_logger(__name__)


def extract_images_pdf(file_path: str) -> dict[int, list[bytes]]:
    """Extract embedded images from a PDF grouped by page index.
    
    Returns: dict mapping page_num (0-indexed) to a list of raw image bytes.
    """
    images_by_page = {}
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page_images = []
            for img_info in doc[page_num].get_images(full=True):
                xref = img_info[0]
                extracted = doc.extract_image(xref)
                if extracted and "image" in extracted:
                    page_images.append(extracted["image"])
            if page_images:
                images_by_page[page_num] = page_images
        doc.close()
        logger.info(f"Extracted images from PDF {os.path.basename(file_path)}: {sum(len(v) for v in images_by_page.values())} total images across {len(images_by_page)} pages")
    except Exception as e:
        logger.error(f"Error extracting PDF images from {file_path}: {e}")
    return images_by_page


def extract_images_from_zip(file_path: str, media_prefix: str) -> list[bytes]:
    """Extract raw image bytes from DOCX ('word/media/') or XLSX ('xl/media/').
    
    Uses standard library zipfile — zero additional dependencies.
    """
    extracted_images = []
    try:
        with zipfile.ZipFile(file_path) as z:
            for name in z.namelist():
                if name.startswith(media_prefix):
                    ext = Path(name).suffix.lower()
                    if ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp"):
                        extracted_images.append(z.read(name))
        logger.info(f"Extracted {len(extracted_images)} media files from zip archive: {os.path.basename(file_path)}")
    except Exception as e:
        logger.error(f"Error extracting zip media from {file_path}: {e}")
    return extracted_images
