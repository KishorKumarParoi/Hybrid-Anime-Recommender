"""
Semantic Vector Caching in Redis for AI Agent Queries.
Avoids expensive LLM re-computations for semantically identical questions.
"""

import json
import logging
from typing import Optional, List
import numpy as np

logger = logging.getLogger(__name__)

_embedding_model = None


def get_embedding_model():
    """Lazy loader for SentenceTransformer to minimize cold-start latency."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded 'all-MiniLM-L6-v2' for Semantic Vector Cache.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer for semantic cache: {e}")
            _embedding_model = False
    return _embedding_model if _embedding_model is not False else None


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Computes cosine similarity between two vector embeddings."""
    va, vb = np.array(a), np.array(b)
    norm = np.linalg.norm(va) * np.linalg.norm(vb)
    if norm == 0:
        return 0.0
    return float(np.dot(va, vb) / norm)


class SemanticAgentCache:
    """
    High-performance semantic caching layer backed by Redis and dense vector embeddings.
    """

    def __init__(self, redis_client=None, similarity_threshold: float = 0.88, ttl: int = 3600):
        self.redis = redis_client
        self.threshold = similarity_threshold
        self.ttl = ttl
        self._EMB_PREFIX = "agent:emb:"
        self._REC_PREFIX = "agent:rec:"

    def _embed(self, text: str) -> Optional[List[float]]:
        model = get_embedding_model()
        if model is None:
            return None
        return model.encode(text).tolist()

    def get(self, query: str) -> Optional[str]:
        """
        Scans Redis for existing query embeddings with cosine similarity >= threshold.
        Returns cached response string if found, otherwise None.
        """
        if not self.redis:
            return None

        try:
            query_emb = self._embed(query)
            if query_emb is None:
                return None

            # Scan stored embedding keys
            keys = self.redis.keys(f"{self._EMB_PREFIX}*")
            if not keys:
                return None

            best_sim = 0.0
            best_key = None

            for key in keys:
                raw_emb = self.redis.get(key)
                if not raw_emb:
                    continue
                stored_emb = json.loads(raw_emb)
                sim = cosine_similarity(query_emb, stored_emb)

                if sim > best_sim:
                    best_sim = sim
                    best_key = key

            if best_sim >= self.threshold and best_key:
                cache_key = best_key.replace(self._EMB_PREFIX, self._REC_PREFIX)
                cached_result = self.redis.get(cache_key)
                if cached_result:
                    logger.info(
                        f"Semantic Cache Hit! Similarity: {best_sim:.3f} >= {self.threshold} (key: {best_key})"
                    )
                    return cached_result

        except Exception as e:
            logger.warning(f"Semantic cache lookup encountered error: {e}")

        return None

    def set(self, query: str, response: str) -> None:
        """Stores the response and query vector embedding in Redis with TTL expiration."""
        if not self.redis or not query or not response:
            return

        try:
            query_emb = self._embed(query)
            if query_emb is None:
                return

            key_suffix = abs(hash(query))
            emb_key = f"{self._EMB_PREFIX}{key_suffix}"
            rec_key = f"{self._REC_PREFIX}{key_suffix}"

            self.redis.setex(rec_key, self.ttl, response)
            self.redis.setex(emb_key, self.ttl, json.dumps(query_emb))
            logger.info(f"Stored semantic cache entry for query hash: {key_suffix} (TTL: {self.ttl}s)")
        except Exception as e:
            logger.warning(f"Failed to set semantic cache in Redis: {e}")
