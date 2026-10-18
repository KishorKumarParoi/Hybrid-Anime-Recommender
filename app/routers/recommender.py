"""
FastAPI Hybrid Recommender API Router
====================================
"""

import time
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from pipeline.prediction_pipeline import hybrid_recommendation
from src.observability.clickhouse_analytics import get_clickhouse_analytics
from src.observability.telemetry import trace_span

router = APIRouter(prefix="/recommender", tags=["Hybrid Recommender Microservice"])


class RecommendationQuery(BaseModel):
    user_id: int = Field(default=11880, description="User ID for collaborative filtering")
    top_k: int = Field(default=10, ge=1, le=50)


class RecommendationItem(BaseModel):
    anime_id: int
    name: str
    genre: str
    rating: float


@router.post("/hybrid")
async def get_hybrid_recommendations(query: RecommendationQuery):
    """
    Generate hybrid collaborative filtering + content-based anime recommendations.
    Emits telemetry to ClickHouse and OpenTelemetry traces.
    """
    start_time = time.time()
    with trace_span("hybrid_recommendation_inference", {"user_id": query.user_id}) as span:
        try:
            results = hybrid_recommendation(query.user_id)
            latency_ms = round((time.time() - start_time) * 1000, 2)

            analytics = get_clickhouse_analytics()
            analytics.record_recommendation_event(
                user_id=query.user_id,
                recommender_type="hybrid-pytorch-cosine",
                candidate_count=len(results),
                latency_ms=latency_ms,
                cached=False
            )

            span.set_attribute("candidate_count", len(results))
            span.set_attribute("latency_ms", latency_ms)

            return {
                "status": "success",
                "user_id": query.user_id,
                "latency_ms": latency_ms,
                "count": len(results[:query.top_k]),
                "recommendations": results[:query.top_k],
            }
        except Exception as e:
            span.set_attribute("error", str(e))
            raise HTTPException(status_code=500, detail=str(e))
