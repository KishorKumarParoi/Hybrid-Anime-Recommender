"""
Kafka & Azure Event Hubs Real-Time Streaming API Router
======================================================
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.streaming.kafka_stream import get_producer
from src.security.auth_service import get_current_user, UserPayload

router = APIRouter(prefix="/streaming", tags=["Real-time Streaming (Kafka / Azure Event Hubs)"])


class StreamInteractionRequest(BaseModel):
    user_id: str = Field(..., description="User unique identifier")
    anime_id: str = Field(..., description="Anime unique identifier")
    rating: float = Field(..., ge=0.0, le=10.0)
    interaction_type: str = Field(default="rating", description="rating, click, bookmark, complete")
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("/interaction", status_code=status.HTTP_200_OK)
async def stream_user_interaction(
    payload: StreamInteractionRequest,
    user: UserPayload = Depends(get_current_user)
):
    """
    Publish real-time user ratings and interactions into Apache Kafka or Azure Event Hubs.
    Partitioned by user_id to ensure strict event ordering.
    """
    producer = get_producer()
    success = producer.publish_interaction(
        user_id=payload.user_id,
        anime_id=payload.anime_id,
        rating=payload.rating,
        interaction_type=payload.interaction_type,
        metadata=payload.metadata
    )

    return {
        "status": "published" if success else "failed",
        "topic": producer.config.topic_interactions,
        "event": payload.model_dump(),
        "producer": producer.get_status(),
    }


@router.get("/status")
async def get_streaming_status():
    """Retrieve Kafka / Azure Event Hubs connection and buffer diagnostics."""
    producer = get_producer()
    return {"status": "success", "streaming": producer.get_status()}


@router.get("/buffered")
async def get_buffered_stream_events(limit: int = 20):
    """Inspect recently buffered in-memory stream events."""
    producer = get_producer()
    return {
        "status": "success",
        "buffer_depth": len(producer._fallback_buffer),
        "events": producer.get_buffered_events(limit=limit),
    }
