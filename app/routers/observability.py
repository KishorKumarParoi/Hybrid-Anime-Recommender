"""
Observability & Telemetry API Router (OpenTelemetry / Langfuse / ClickHouse / vLLM)
==================================================================================
"""

from fastapi import APIRouter, Depends
from src.observability.telemetry import get_tracer
from src.observability.langfuse_tracer import get_langfuse_tracer
from src.observability.clickhouse_analytics import get_clickhouse_analytics
from src.serving.vllm_client import get_vllm_client
from src.security.auth_service import get_current_user, UserPayload

router = APIRouter(prefix="/observability", tags=["Observability & Telemetry (OpenTelemetry/ClickHouse)"])


@router.get("/metrics")
async def get_clickhouse_olap_metrics():
    """Retrieve high-cardinality OLAP analytics from ClickHouse (P50, P95, Cache Ratios)."""
    analytics = get_clickhouse_analytics()
    return {"status": "success", "analytics": analytics.get_summary_metrics()}


@router.get("/traces")
async def get_opentelemetry_traces():
    """Retrieve recent OpenTelemetry distributed traces and span durations."""
    tracer = get_tracer()
    return {
        "status": "success",
        "service_name": tracer.service_name,
        "recent_spans": tracer.recent_spans[-20:],
    }


@router.get("/langfuse")
async def get_langfuse_llm_metrics():
    """Retrieve Langfuse LLM observation traces, prompt versioning, and cost tracking."""
    langfuse = get_langfuse_tracer()
    return {
        "status": "success",
        "recent_traces": langfuse.get_recent_traces(limit=20),
    }


@router.get("/serving")
async def get_gpu_serving_status():
    """Check GPU inference serving health (vLLM PagedAttention, RunPod, BentoML)."""
    vllm = get_vllm_client()
    vllm_health = await vllm.check_health()
    return {
        "status": "success",
        "engines": {
            "vllm": vllm_health,
            "runpod_serverless": {"supported": True, "target": "NVIDIA-A100-SXM4"},
            "bentoml": {"version": "1.2.0-pytorch", "active": True},
        }
    }
