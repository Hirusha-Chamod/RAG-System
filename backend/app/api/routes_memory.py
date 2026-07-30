"""
Long-term memory management endpoints:
- GET /memory
- POST /memory
- DELETE /memory
- DELETE /memory/{key}

Secured with Depends(get_current_user) JWT Bearer authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from app.api.deps import get_current_user
from app.memory.long_term import (
    get_all_memory,
    set_memory,
    delete_memory_key,
    delete_all_memory,
)
from app.models.schemas import MemoryResponse, MemoryEntry
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/memory", tags=["Memory"])


class SetMemoryRequest(BaseModel):
    """Request body for POST /memory."""
    key: str
    value: str


@router.get("", response_model=MemoryResponse)
async def get_user_memories(current_user: dict = Depends(get_current_user)):
    """Retrieve all long-term memory entries for the authenticated user."""
    user_id = current_user["user_id"]
    memories_dict = get_all_memory(user_id)

    entries = [
        MemoryEntry(key=k, value={"text": v}, updated_at=0.0)
        for k, v in memories_dict.items()
    ]
    return MemoryResponse(user_id=user_id, memories=entries)


@router.post("", status_code=status.HTTP_201_CREATED)
async def save_user_memory(
    request: SetMemoryRequest,
    current_user: dict = Depends(get_current_user),
):
    """Store or update a long-term memory entry for the authenticated user."""
    user_id = current_user["user_id"]
    set_memory(user_id, request.key, request.value)
    return {"status": "success", "user_id": user_id, "key": request.key}


@router.delete("")
async def clear_all_user_memories(
    key: str | None = Query(None, description="Optional key to delete single memory entry"),
    current_user: dict = Depends(get_current_user),
):
    """Clear all long-term memory entries or a specific key for the authenticated user."""
    user_id = current_user["user_id"]
    if key:
        delete_memory_key(user_id, key)
        return {"status": "deleted_key", "user_id": user_id, "key": key}
    else:
        delete_all_memory(user_id)
        return {"status": "cleared_all", "user_id": user_id}
