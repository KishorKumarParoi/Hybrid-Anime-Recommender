import asyncio
import logging
from app.config import Config
from app.retry import with_retry
from src.ai_agent.guardrails import validate_input as local_validate_input, validate_output as local_validate_output

logger = logging.getLogger(__name__)


def _apply_guardrail_sync(config: Config, text: str, source: str) -> dict:
    """Invokes AWS Bedrock apply_guardrail if configured."""
    try:
        import boto3
        client = boto3.client("bedrock-runtime", region_name=config.aws_region)
        return client.apply_guardrail(
            guardrailIdentifier=config.bedrock_guardrail_id,
            guardrailVersion=config.bedrock_guardrail_version,
            source=source,
            content=[{"text": {"text": text}}],
        )
    except Exception as e:
        logger.debug(f"Bedrock guardrail call bypassed (offline or not configured): {e}")
        return {"action": "NONE"}


async def validate_input(config: Config, text: str) -> tuple[bool, str]:
    """
    Dual-layer ingress safety validation:
    1. Local regex/heuristic prompt injection & harmful content filter
    2. Cloud AWS Bedrock Guardrail policy (if active)
    """
    # 1. Local hardened guardrail
    is_safe, error_msg, _ = local_validate_input(text)
    if not is_safe:
        return False, error_msg

    # 2. AWS Bedrock Guardrail check (if bedrock_guardrail_id configured)
    if config.bedrock_guardrail_id and config.bedrock_guardrail_id != "default-guardrail":
        try:
            response = await with_retry(
                lambda: asyncio.to_thread(_apply_guardrail_sync, config, text, "INPUT"),
                max_retries=config.llm_max_retries,
                delay=config.llm_retry_delay,
            )
            if response.get("action") == "GUARDRAIL_INTERVENED":
                return False, "Input blocked by AWS Bedrock safety guardrail policy."
        except Exception as e:
            logger.warning(f"Bedrock input guardrail check warning: {e}")

    return True, ""


async def validate_output(config: Config, text: str) -> tuple[bool, str]:
    """
    Dual-layer egress safety validation:
    1. Local credential leakage & system prompt dump scanner
    2. Cloud AWS Bedrock Guardrail output policy (if active)
    """
    # 1. Local output check
    is_safe, reason = local_validate_output(text)
    if not is_safe:
        return False, reason

    # 2. AWS Bedrock Guardrail check
    if config.bedrock_guardrail_id and config.bedrock_guardrail_id != "default-guardrail":
        try:
            response = await with_retry(
                lambda: asyncio.to_thread(_apply_guardrail_sync, config, text, "OUTPUT"),
                max_retries=config.llm_max_retries,
                delay=config.llm_retry_delay,
            )
            if response.get("action") == "GUARDRAIL_INTERVENED":
                return False, "Output blocked by AWS Bedrock safety guardrail policy."
        except Exception as e:
            logger.warning(f"Bedrock output guardrail check warning: {e}")

    return True, ""
