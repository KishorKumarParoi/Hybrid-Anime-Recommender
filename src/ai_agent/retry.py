"""
Resilient LLM Execution with Exponential Backoff & Jitter.
Inspired by enterprise retry architectures in 190 - AI Security Project Materials.
"""

import time
import random
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def with_retry(
    func: Callable[[], Any],
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
) -> Any:
    """
    Executes func() with exponential backoff and optional jitter.
    Specifically catches RateLimitError (429), timeouts, and transient connection drops.
    """
    last_exc = None
    wait = delay

    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as exc:
            last_exc = exc
            exc_str = str(exc).lower()

            # Check if this is an error worth retrying
            is_retryable = (
                "429" in exc_str
                or "rate" in exc_str
                or "timeout" in exc_str
                or "connection" in exc_str
                or "service unavailable" in exc_str
                or "503" in exc_str
            )

            if attempt < max_retries and is_retryable:
                sleep_time = wait + (random.uniform(0, 0.5) if jitter else 0)
                logger.warning(
                    f"LLM attempt {attempt}/{max_retries} failed with ({exc}). Retrying in {sleep_time:.2f}s..."
                )
                time.sleep(sleep_time)
                wait *= backoff
            elif not is_retryable:
                # Do not retry on non-transient errors (e.g. invalid auth, bad request)
                logger.error(f"Non-retryable LLM exception caught: {exc}")
                raise exc

    logger.error(f"All {max_retries} retry attempts exhausted. Raising last exception: {last_exc}")
    raise last_exc
