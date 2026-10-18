import os
import socket
import json
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_secret() -> dict:
    """
    Attempts to load runtime configuration from AWS Secrets Manager.
    If unavailable or offline, seamlessly falls back to local environment variables and .env.
    """
    secret_name = os.environ.get("SECRETS_NAME", "hybrid-anime-recommender/config")
    region = os.environ.get("AWS_REGION", "us-east-1")

    try:
        import boto3
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        if "SecretString" in response:
            logger.info(f"Loaded configuration from AWS Secrets Manager: {secret_name}")
            return json.loads(response["SecretString"])
    except Exception as e:
        logger.debug(f"AWS Secrets Manager not accessible, loading from environment: {e}")

    # Fallback to local environment variables and defaults
    return {
        "AWS_REGION": os.environ.get("AWS_REGION", "us-east-1"),
        "BEDROCK_GUARDRAIL_ID": os.environ.get("BEDROCK_GUARDRAIL_ID", "default-guardrail"),
        "BEDROCK_GUARDRAIL_VERSION": os.environ.get("BEDROCK_GUARDRAIL_VERSION", "1"),
        "REDIS_URL": os.environ.get("REDIS_URL", f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', 6379)}"),
        "DATABASE_URL": os.environ.get("DATABASE_URL", "postgresql://dbadmin:password@localhost:5432/animeresearchdb"),
        "TENSORZERO_URL": os.environ.get("TENSORZERO_URL", "http://localhost:3000"),
        "API_KEY": os.environ.get("API_KEY", ""),
        "GROQ_API_KEY": os.environ.get("GROQ_API_KEY", ""),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY", ""),
        "AZURE_OPENAI_API_KEY": os.environ.get("AZURE_OPENAI_API_KEY", ""),
        "AZURE_OPENAI_ENDPOINT": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
        "TARGET_URL": os.environ.get("TARGET_URL", "http://localhost:5001"),
        "LANGSMITH_API_KEY": os.environ.get("LANGSMITH_API_KEY", ""),
        "LANGCHAIN_PROJECT": os.environ.get("LANGCHAIN_PROJECT", "hybrid-anime-recommender"),
        "LANGSMITH_DATASET": os.environ.get("LANGSMITH_DATASET", "anime-research-reports"),
        "CACHE_TTL": os.environ.get("CACHE_TTL", "3600"),
        "CACHE_SIMILARITY_THRESHOLD": os.environ.get("CACHE_SIMILARITY_THRESHOLD", "0.85"),
        "SESSION_TTL": os.environ.get("SESSION_TTL", "1800"),
        "SESSION_MAX_MESSAGES": os.environ.get("SESSION_MAX_MESSAGES", "5"),
        "SESSION_CONTENT_TRUNCATE": os.environ.get("SESSION_CONTENT_TRUNCATE", "500"),
        "LTM_DAYS": os.environ.get("LTM_DAYS", "7"),
        "LTM_THRESHOLD": os.environ.get("LTM_THRESHOLD", "0.88"),
        "LTM_DIFF_THRESHOLD": os.environ.get("LTM_DIFF_THRESHOLD", "0.7"),
        "LTM_DIFF_LIMIT": os.environ.get("LTM_DIFF_LIMIT", "5"),
        "IVFFLAT_LISTS": os.environ.get("IVFFLAT_LISTS", "100"),
        "STREAM_KEY": os.environ.get("STREAM_KEY", "research:jobs"),
        "CONSUMER_GROUP": os.environ.get("CONSUMER_GROUP", "workers"),
        "CONSUMER_NAME": socket.gethostname(),
        "RESULT_TTL": os.environ.get("RESULT_TTL", "3600"),
        "AGENT_REPORT_TRUNCATE": os.environ.get("AGENT_REPORT_TRUNCATE", "3000"),
        "AGENT_MAX_ITERATIONS": os.environ.get("AGENT_MAX_ITERATIONS", "2"),
        "EVAL_REPORT_TRUNCATE": os.environ.get("EVAL_REPORT_TRUNCATE", "1500"),
        "EVAL_COMMENT_TRUNCATE": os.environ.get("EVAL_COMMENT_TRUNCATE", "300"),
        "LLM_MAX_RETRIES": os.environ.get("LLM_MAX_RETRIES", "3"),
        "LLM_RETRY_DELAY": os.environ.get("LLM_RETRY_DELAY", "1.0"),
        "RATE_LIMIT_REQUESTS": os.environ.get("RATE_LIMIT_REQUESTS", "10"),
        "RATE_LIMIT_WINDOW": os.environ.get("RATE_LIMIT_WINDOW", "60"),
        "DB_POOL_MIN": os.environ.get("DB_POOL_MIN", "2"),
        "DB_POOL_MAX": os.environ.get("DB_POOL_MAX", "10"),
    }


class Config:
    def __init__(self):
        data = _load_secret()

        # AWS / Cloud
        self.aws_region: str = data.get("AWS_REGION", "us-east-1")
        self.bedrock_guardrail_id: str = data.get("BEDROCK_GUARDRAIL_ID", "")
        self.bedrock_guardrail_version: str = data.get("BEDROCK_GUARDRAIL_VERSION", "1")

        # Storage & Endpoints
        self.redis_url: str = data.get("REDIS_URL", "redis://localhost:6379")
        self.database_url: str = data.get("DATABASE_URL", "")
        self.tensorzero_url: str = data.get("TENSORZERO_URL", "http://localhost:3000")

        # Auth & LLM Keys
        self.api_key: str = data.get("API_KEY", "")
        self.groq_api_key: str = data.get("GROQ_API_KEY", "")
        self.openai_api_key: str = data.get("OPENAI_API_KEY", "")
        self.anthropic_api_key: str = data.get("ANTHROPIC_API_KEY", "")
        self.tavily_api_key: str = data.get("TAVILY_API_KEY", "")
        self.azure_openai_api_key: str = data.get("AZURE_OPENAI_API_KEY", "")
        self.azure_openai_endpoint: str = data.get("AZURE_OPENAI_ENDPOINT", "")
        self.target_url: str = data.get("TARGET_URL", "http://localhost:5001")

        # LangSmith Observability
        self.langsmith_api_key: str = data.get("LANGSMITH_API_KEY", "")
        self.langchain_project: str = data.get("LANGCHAIN_PROJECT", "hybrid-anime-recommender")
        self.langsmith_dataset: str = data.get("LANGSMITH_DATASET", "anime-research-reports")

        # Semantic Cache
        self.cache_ttl: int = int(data.get("CACHE_TTL", 3600))
        self.cache_similarity_threshold: float = float(data.get("CACHE_SIMILARITY_THRESHOLD", 0.85))

        # Session Memory
        self.session_ttl: int = int(data.get("SESSION_TTL", 1800))
        self.session_max_messages: int = int(data.get("SESSION_MAX_MESSAGES", 5))
        self.session_content_truncate: int = int(data.get("SESSION_CONTENT_TRUNCATE", 500))

        # Long-Term Memory (pgvector)
        self.ltm_days: int = int(data.get("LTM_DAYS", 7))
        self.ltm_threshold: float = float(data.get("LTM_THRESHOLD", 0.88))
        self.ltm_diff_threshold: float = float(data.get("LTM_DIFF_THRESHOLD", 0.7))
        self.ltm_diff_limit: int = int(data.get("LTM_DIFF_LIMIT", 5))
        self.ivfflat_lists: int = int(data.get("IVFFLAT_LISTS", 100))

        # Job Queue (Redis Streams)
        self.stream_key: str = data.get("STREAM_KEY", "research:jobs")
        self.consumer_group: str = data.get("CONSUMER_GROUP", "workers")
        self.consumer_name: str = data.get("CONSUMER_NAME", socket.gethostname())
        self.result_ttl: int = int(data.get("RESULT_TTL", 3600))

        # Agent Tuning
        self.agent_report_truncate: int = int(data.get("AGENT_REPORT_TRUNCATE", 3000))
        self.agent_max_iterations: int = int(data.get("AGENT_MAX_ITERATIONS", 2))

        # Eval Tuning
        self.eval_report_truncate: int = int(data.get("EVAL_REPORT_TRUNCATE", 1500))
        self.eval_comment_truncate: int = int(data.get("EVAL_COMMENT_TRUNCATE", 300))

        # LLM Retry
        self.llm_max_retries: int = int(data.get("LLM_MAX_RETRIES", 3))
        self.llm_retry_delay: float = float(data.get("LLM_RETRY_DELAY", 1.0))

        # Rate Limiting
        self.rate_limit_requests: int = int(data.get("RATE_LIMIT_REQUESTS", 10))
        self.rate_limit_window: int = int(data.get("RATE_LIMIT_WINDOW", 60))

        # Database Connection Pool
        self.db_pool_min: int = int(data.get("DB_POOL_MIN", 2))
        self.db_pool_max: int = int(data.get("DB_POOL_MAX", 10))

        # Initialize LangSmith environment variables if key is present
        if self.langsmith_api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = self.langchain_project
            os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
