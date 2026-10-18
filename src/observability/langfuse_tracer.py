"""
Langfuse LLM Observability & Evaluation Client
==============================================
Logs LLM prompt versions, completions, token usage, latency,
and user feedback scores for continuous LLMOps evaluation.
"""

import os
import time
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("Langfuse")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")


class LangfuseTracer:
    """Records LLM traces and metrics to Langfuse cloud or local buffer."""

    def __init__(self):
        self.public_key = LANGFUSE_PUBLIC_KEY
        self.secret_key = LANGFUSE_SECRET_KEY
        self.host = LANGFUSE_HOST
        self._traces_buffer: List[Dict[str, Any]] = []

    def record_generation(
        self,
        trace_id: str,
        name: str,
        model: str,
        input_prompt: str,
        output_completion: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Record an LLM call generation trace."""
        # Cost estimate based on standard Llama 3.1 / GPT-4o-mini rates
        est_cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060)

        record = {
            "trace_id": trace_id,
            "name": name,
            "model": model,
            "input_prompt_snippet": input_prompt[:150],
            "output_completion_snippet": output_completion[:150],
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency_ms": latency_ms,
            "estimated_cost_usd": round(est_cost, 6),
            "metadata": metadata or {},
            "timestamp": time.time(),
        }

        self._traces_buffer.append(record)
        if len(self._traces_buffer) > 200:
            self._traces_buffer.pop(0)

        return record

    def record_score(self, trace_id: str, name: str, value: float, comment: Optional[str] = None):
        """Record evaluation judge score or user feedback (0.0 to 1.0)."""
        logger.info(f"Langfuse score logged for {trace_id}: {name}={value} ({comment})")

    def get_recent_traces(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._traces_buffer[-limit:]


_global_langfuse: Optional[LangfuseTracer] = None


def get_langfuse_tracer() -> LangfuseTracer:
    global _global_langfuse
    if _global_langfuse is None:
        _global_langfuse = LangfuseTracer()
    return _global_langfuse
