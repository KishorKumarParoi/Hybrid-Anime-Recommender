"""
DocumentDB & MongoDB Document Management API Router
===================================================
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.database.document_store import (
    AnimeDoc,
    UserInteractionDoc,
    ResearchDossierDoc,
    SecurityAuditDoc,
    get_document_store,
)
from src.security.auth_service import get_current_user, UserPayload, RoleChecker

router = APIRouter(prefix="/documents", tags=["Document Database (MongoDB/DocumentDB)"])


@router.post("/anime", status_code=status.HTTP_200_OK)
async def upsert_anime_document(
    anime: AnimeDoc,
    user: UserPayload = Depends(RoleChecker(["admin", "researcher"]))
):
    """Upsert anime document into DocumentDB/MongoDB."""
    store = get_document_store()
    saved = await store.upsert_anime(anime)
    return {"status": "saved", "anime": saved}


@router.get("/anime/{anime_id}")
async def get_anime_document(anime_id: str):
    """Retrieve an anime document by ID."""
    store = get_document_store()
    doc = await store.get_anime(anime_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Anime {anime_id} not found in DocumentDB.")
    return {"status": "found", "anime": doc}


@router.post("/interaction", status_code=status.HTTP_201_CREATED)
async def record_user_interaction(
    interaction: UserInteractionDoc,
    user: UserPayload = Depends(get_current_user)
):
    """Record an interaction or rating document."""
    store = get_document_store()
    saved = await store.record_interaction(interaction)
    return {"status": "recorded", "interaction": saved}


@router.get("/interaction/{user_id}")
async def get_user_interaction_history(
    user_id: str,
    limit: int = 20,
    user: UserPayload = Depends(get_current_user)
):
    """Retrieve chronological interaction history for a user."""
    store = get_document_store()
    history = await store.get_user_interactions(user_id=user_id, limit=limit)
    return {"status": "success", "user_id": user_id, "count": len(history), "history": history}


@router.get("/status")
async def get_database_status():
    """Diagnostic health and collection metrics of MongoDB / Amazon DocumentDB."""
    store = get_document_store()
    return {"status": "success", "database": store.get_status()}
