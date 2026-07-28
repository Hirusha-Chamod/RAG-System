"""
Multipart file upload ingestion endpoint: POST /ingest

Processes PDF, DOCX, XLSX, TXT, MD, PNG, JPG files:
1. Extracts text via loaders
2. Extracts images (PyMuPDF for PDF, zipfile for DOCX/XLSX)
3. Generates vision descriptions with SHA256 caching & 3KB size threshold
4. Inlines descriptions into parent document text
5. Splits text into parents (~2000 ch) and children (~400 ch)
6. Saves parents in SQLite, embeds children into ChromaDB with user_id metadata
"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form
from app.ingestion.loaders import load_file, SUPPORTED_EXTENSIONS
from app.ingestion.image_extraction import extract_images_pdf, extract_images_from_zip
from app.ingestion.image_describer import describe_image
from app.ingestion.chunking import split_into_parents_and_children
from app.ingestion.parent_store import save_parent
from app.ingestion.vectorstore import get_vectorstore
from app.models.schemas import IngestResponse, IngestFileResult
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_files(
    files: list[UploadFile] = File(...),
    user_id: str = Form(...),
):
    """Ingest one or more files into the RAG pipeline."""
    results = []
    total_chunks = 0
    total_images = 0

    for upload_file in files:
        file_result = await _process_single_file(upload_file, user_id)
        total_chunks += file_result.chunks_created
        total_images += file_result.images_processed
        results.append(file_result)

    return IngestResponse(
        results=results,
        total_chunks=total_chunks,
        total_images=total_images,
    )


async def _process_single_file(upload_file: UploadFile, user_id: str) -> IngestFileResult:
    """Process a single file with isolation — never raises an unhandled exception."""
    file_id = str(uuid.uuid4())[:8]
    filename = upload_file.filename or "file"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        return IngestFileResult(
            filename=filename,
            status="error",
            error_message=f"Unsupported file type: {ext}",
        )

    # Save raw upload to disk
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{filename}")
    try:
        content = await upload_file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        return IngestFileResult(
            filename=filename, status="error", error_message=f"Save failed: {e}"
        )

    chunks_created = 0
    images_processed = 0
    vs = get_vectorstore()

    try:
        # 1. Handle standalone images directly uploaded (.png, .jpg, .jpeg)
        if ext in (".png", ".jpg", ".jpeg"):
            description = await describe_image(content)
            if description:
                parent_id = f"{file_id}_img"
                save_parent(parent_id, f"[Image Description]: {description}", filename, user_id)
                vs.add_texts(
                    texts=[description],
                    metadatas=[{"source": filename, "parent_id": parent_id, "user_id": user_id}],
                )
                images_processed += 1
                chunks_created += 1

            return IngestFileResult(
                filename=filename,
                status="success",
                chunks_created=chunks_created,
                images_processed=images_processed,
            )

        # 2. Document files: load text documents
        docs = load_file(file_path)

        # 3. Extract embedded images by file type
        pdf_images_by_page = {}
        zip_images = []
        if ext == ".pdf":
            pdf_images_by_page = extract_images_pdf(file_path)
        elif ext == ".docx":
            zip_images = extract_images_from_zip(file_path, "word/media/")
        elif ext == ".xlsx":
            zip_images = extract_images_from_zip(file_path, "xl/media/")

        # 4. Describe standalone ZIP images (for docx/xlsx) once
        zip_image_descriptions = []
        for img_bytes in zip_images:
            if (desc := await describe_image(img_bytes)):
                zip_image_descriptions.append(desc)
                images_processed += 1

        # 5. Process each loaded Document / Page
        for doc_index, doc in enumerate(docs):
            page_text = doc.page_content or ""

            # Check for PDF images on this page
            page_descriptions = []
            if ext == ".pdf" and doc_index in pdf_images_by_page:
                for img_bytes in pdf_images_by_page[doc_index]:
                    if (desc := await describe_image(img_bytes)):
                        page_descriptions.append(desc)
                        images_processed += 1

            # Append image descriptions to document text before splitting
            all_descriptions = page_descriptions if ext == ".pdf" else zip_image_descriptions
            if all_descriptions:
                desc_text = "\n\n" + "\n".join(f"[Image Content: {d}]" for d in all_descriptions)
                doc.page_content = page_text + desc_text

            # 6. Split into parents (~2000 ch) and children (~400 ch)
            parents, children = split_into_parents_and_children(doc, file_id, doc_index)

            # 7. Persist parents to SQLite & children to ChromaDB
            for p in parents:
                save_parent(p["parent_id"], p["content"], p["source"], user_id)

            if children:
                vs.add_texts(
                    texts=[c["content"] for c in children],
                    metadatas=[{**c["metadata"], "user_id": user_id} for c in children],
                )
                chunks_created += len(children)

        return IngestFileResult(
            filename=filename,
            status="success",
            chunks_created=chunks_created,
            images_processed=images_processed,
        )

    except Exception as e:
        logger.error(f"Ingestion error processing {filename}: {e}", exc_info=True)
        return IngestFileResult(
            filename=filename,
            status="error",
            chunks_created=chunks_created,
            images_processed=images_processed,
            error_message=str(e),
        )
