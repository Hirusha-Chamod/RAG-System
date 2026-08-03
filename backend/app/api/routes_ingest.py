"""
Multipart file upload ingestion & Document Management endpoints:
- POST /ingest — Upload and chunk documents
- GET /ingest/documents — List uploaded files for user
- DELETE /ingest/documents — Wipe an ingested document from ChromaDB & SQLite

Secured with Depends(get_current_user) JWT Bearer authentication.
"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, Query, HTTPException
from app.ingestion.loaders import load_file, SUPPORTED_EXTENSIONS
from app.ingestion.image_extraction import extract_images_pdf, extract_images_from_zip
from app.ingestion.image_describer import describe_image
from app.ingestion.chunking import split_into_parents_and_children
from app.ingestion.parent_store import save_parent, get_user_documents, delete_user_document
from app.ingestion.vectorstore import get_vectorstore
from app.models.schemas import IngestResponse, IngestFileResult
from app.api.deps import get_current_user
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_files(
    files: list[UploadFile] = File(...),
    session_id: str | None = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """Ingest one or more files into the RAG pipeline for the authenticated user, optionally scoped to session_id."""
    user_id = current_user["user_id"]
    results = []
    total_chunks = 0
    total_images = 0

    for upload_file in files:
        file_result = await _process_single_file(upload_file, user_id, session_id=session_id)
        total_chunks += file_result.chunks_created
        total_images += file_result.images_processed
        results.append(file_result)

    return IngestResponse(
        results=results,
        total_chunks=total_chunks,
        total_images=total_images,
    )


@router.get("/ingest/documents")
async def list_documents(current_user: dict = Depends(get_current_user)):
    """Retrieve list of ingested documents for the authenticated user."""
    user_id = current_user["user_id"]
    docs = get_user_documents(user_id)
    return {"user_id": user_id, "documents": docs}


@router.delete("/ingest/documents")
async def delete_document(
    source: str = Query(..., description="Source filename or filepath to delete"),
    current_user: dict = Depends(get_current_user),
):
    """Delete a document from parent store and ChromaDB vector store for the user."""
    user_id = current_user["user_id"]

    # 1. Delete parent records from SQLite
    deleted_parents = delete_user_document(user_id, source)

    # 2. Delete matching vector chunks from ChromaDB
    vs = get_vectorstore()
    try:
        if hasattr(vs, "_collection") and vs._collection is not None:
            vs._collection.delete(where={"user_id": user_id, "source": source})
    except Exception as e:
        logger.warning(f"ChromaDB delete exception for {source}: {e}")

    logger.info(f"Deleted document '{source}' for user '{user_id}' ({deleted_parents} parents removed)")
    return {
        "user_id": user_id,
        "source": source,
        "status": "deleted",
        "deleted_parents": deleted_parents,
    }


async def _process_single_file(upload_file: UploadFile, user_id: str, session_id: str | None = None) -> IngestFileResult:
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
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            return IngestFileResult(
                filename=filename,
                status="error",
                error_message=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB",
            )
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
                save_parent(parent_id, f"[Image Description]: {description}", filename, user_id, session_id=session_id)
                meta = {"source": filename, "parent_id": parent_id, "user_id": user_id}
                if session_id:
                    meta["session_id"] = session_id
                vs.add_texts(
                    texts=[description],
                    metadatas=[meta],
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

            page_descriptions = []
            if ext == ".pdf" and doc_index in pdf_images_by_page:
                for img_bytes in pdf_images_by_page[doc_index]:
                    if (desc := await describe_image(img_bytes)):
                        page_descriptions.append(desc)
                        images_processed += 1

            all_descriptions = page_descriptions if ext == ".pdf" else zip_image_descriptions
            if all_descriptions:
                desc_text = "\n\n" + "\n".join(f"[Image Content: {d}]" for d in all_descriptions)
                doc.page_content = page_text + desc_text

            parents, children = split_into_parents_and_children(doc, file_id, doc_index)

            for p in parents:
                save_parent(p["parent_id"], p["content"], filename, user_id, session_id=session_id)

            if children:
                child_metadatas = []
                for c in children:
                    m = {**c["metadata"], "source": filename, "user_id": user_id}
                    if session_id:
                        m["session_id"] = session_id
                    child_metadatas.append(m)

                vs.add_texts(
                    texts=[c["content"] for c in children],
                    metadatas=child_metadatas,
                )
                chunks_created += len(children)

        # Clean up temporary disk upload file after processing
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Could not remove temp upload file {file_path}: {e}")

        return IngestFileResult(
            filename=filename,
            status="success",
            chunks_created=chunks_created,
            images_processed=images_processed,
        )

    except Exception as e:
        logger.error(f"Ingestion error processing {filename}: {e}", exc_info=True)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        return IngestFileResult(
            filename=filename,
            status="error",
            chunks_created=chunks_created,
            images_processed=images_processed,
            error_message=str(e),
        )
