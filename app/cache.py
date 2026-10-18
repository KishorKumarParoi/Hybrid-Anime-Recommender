import json
import logging
import numpy as np
import redis.asyncio as aioredis
from sentence_transformers import SentenceTransformer
from app.config import Config

logger = logging.getLogger(__name__)

# Lazy initialization of sentence transformer model to conserve memory until first use
_model = None
_CACHE_PREFIX = "semantic:"
_EMB_PREFIX = "emb:"


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _cosine_similarity(a: list, b: list) -> float:
    va, vb = np.array(a), np.array(b)
    norm = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / norm) if norm > 0 else 0.0


def _embed(text: str) -> list:
    return _get_model().encode(text).tolist()


async def cache_get(redis: aioredis.Redis, config: Config, query: str) -> str | None:
    if not redis:
        return None
    try:
        query_emb = _embed(query)
        async for key in redis.scan_iter(f"{_EMB_PREFIX}*"):
            stored_raw = await redis.get(key)
            if not stored_raw:
                continue
            stored_emb = json.loads(stored_raw)
            if _cosine_similarity(query_emb, stored_emb) >= config.cache_similarity_threshold:
                cache_key = key.replace(_EMB_PREFIX, _CACHE_PREFIX)
                return await redis.get(cache_key)
    except Exception as e:
        logger.warning(f"Semantic cache lookup exception: {e}")
    return None


async def cache_set(redis: aioredis.Redis, config: Config, query: str, result: str) -> None:
    if not redis:
        return
    try:
        key_suffix = abs(hash(query))
        await redis.setex(f"{_CACHE_PREFIX}{key_suffix}", config.cache_ttl, result)
        await redis.setex(f"{_EMB_PREFIX}{key_suffix}", config.cache_ttl, json.dumps(_embed(query)))
    except Exception as e:
        logger.warning(f"Semantic cache write exception: {e}")
