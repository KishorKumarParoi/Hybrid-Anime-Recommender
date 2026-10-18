import logging
import asyncpg
from app.config import Config

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def init_pool(config: Config) -> None:
    global _pool
    if not config.database_url:
        logger.warning("DATABASE_URL not set; database connection pool skipped.")
        return

    try:
        _pool = await asyncpg.create_pool(
            config.database_url,
            min_size=config.db_pool_min,
            max_size=config.db_pool_max,
            timeout=5.0,
        )
        logger.info("PostgreSQL asyncpg connection pool initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL ({e}). LTM features will operate in-memory or degraded.")
        _pool = None


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool | None:
    return _pool
