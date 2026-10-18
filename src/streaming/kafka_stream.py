"""
Apache Kafka & Azure Event Hubs Real-Time Streaming Engine
==========================================================
Provides resilient real-time streaming producers and consumers for:
  1. User Anime Interactions & Ratings (topic: anime-interactions-stream)
  2. PyRIT Red-Teaming & AI Security Audits (topic: security-audit-stream)
  3. Autonomous LangGraph Research Events (topic: agent-research-stream)

Designed for multi-cloud compatibility:
  - Local / Containerized Kafka or Redpanda (PLAINTEXT on port 9092)
  - Azure Event Hubs (Kafka 1.0+ surface on port 9093 with SASL_SSL PLAIN)
  - AWS Amazon Managed Streaming for Apache Kafka (MSK)
  - Graceful In-Memory Fallback when brokers are offline or unreachable
"""

import os
import ssl
import json
import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("KafkaStream")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


@dataclass
class KafkaConfig:
    """Configuration settings for Kafka / Azure Event Hubs streaming connection."""
    bootstrap_servers: str = field(
        default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    )
    security_protocol: str = field(
        default_factory=lambda: os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
    )
    sasl_mechanism: str = field(
        default_factory=lambda: os.getenv("KAFKA_SASL_MECHANISM", "PLAIN")
    )
    sasl_username: str = field(
        default_factory=lambda: os.getenv("KAFKA_SASL_USERNAME", "")
    )
    sasl_password: str = field(
        default_factory=lambda: os.getenv("KAFKA_SASL_PASSWORD", "")
    )
    topic_interactions: str = field(
        default_factory=lambda: os.getenv("KAFKA_TOPIC_INTERACTIONS", "anime-interactions-stream")
    )
    topic_security_audit: str = field(
        default_factory=lambda: os.getenv("KAFKA_TOPIC_SECURITY_AUDIT", "security-audit-stream")
    )
    topic_agent_research: str = field(
        default_factory=lambda: os.getenv("KAFKA_TOPIC_AGENT_RESEARCH", "agent-research-stream")
    )
    consumer_group: str = field(
        default_factory=lambda: os.getenv("KAFKA_CONSUMER_GROUP", "recommender-online-worker")
    )
    request_timeout_ms: int = 4000
    retry_backoff_ms: int = 500

    @property
    def is_sasl_ssl(self) -> bool:
        return self.security_protocol.upper() in ("SASL_SSL", "SSL") or bool(self.sasl_password)


class KafkaStreamProducer:
    """
    High-throughput asynchronous Kafka producer with offline fallback buffering.
    Can be used asynchronously or via synchronous convenience helpers.
    """

    def __init__(self, config: Optional[KafkaConfig] = None):
        self.config = config or KafkaConfig()
        self._producer = None
        self._is_online = False
        self._init_attempted = False
        self._fallback_buffer: deque = deque(maxlen=2000)
        self._total_published = 0
        self._lock = asyncio.Lock()

    async def start(self) -> bool:
        """Initialize the AIOKafkaProducer connection with timeout protection."""
        async with self._lock:
            if self._is_online and self._producer:
                return True

            try:
                from aiokafka import AIOKafkaProducer

                producer_kwargs: Dict[str, Any] = {
                    "bootstrap_servers": self.config.bootstrap_servers,
                    "request_timeout_ms": self.config.request_timeout_ms,
                    "retry_backoff_ms": self.config.retry_backoff_ms,
                    "value_serializer": lambda v: json.dumps(v, default=str).encode("utf-8"),
                    "key_serializer": lambda k: str(k).encode("utf-8") if k is not None else None,
                }

                if self.config.is_sasl_ssl and self.config.sasl_password:
                    ssl_context = ssl.create_default_context()
                    producer_kwargs.update({
                        "security_protocol": "SASL_SSL",
                        "sasl_mechanism": self.config.sasl_mechanism or "PLAIN",
                        "sasl_plain_username": self.config.sasl_username or "$ConnectionString",
                        "sasl_plain_password": self.config.sasl_password,
                        "ssl_context": ssl_context,
                    })

                self._producer = AIOKafkaProducer(**producer_kwargs)
                # Attempt connection with a strict timeout to avoid blocking startup
                await asyncio.wait_for(self._producer.start(), timeout=2.0)
                self._is_online = True
                logger.info(f"KafkaStreamProducer connected to {self.config.bootstrap_servers}")
                return True

            except Exception as exc:
                self._is_online = False
                if self._producer:
                    try:
                        await self._producer.stop()
                    except Exception:
                        pass
                self._producer = None
                logger.warning(
                    f"Kafka broker unreachable at {self.config.bootstrap_servers} ({exc}). "
                    "Operating in resilient offline buffer mode."
                )
                return False
            finally:
                self._init_attempted = True

    async def stop(self):
        """Flush remaining events and safely stop producer."""
        async with self._lock:
            if self._producer and self._is_online:
                try:
                    await self._producer.stop()
                except Exception as exc:
                    logger.debug(f"Error during producer stop: {exc}")
                finally:
                    self._producer = None
                    self._is_online = False

    async def publish_raw(self, topic: str, key: Optional[str], value: Dict[str, Any]) -> bool:
        """Publish an arbitrary event to a topic, falling back to memory buffer if offline."""
        if not self._init_attempted:
            await self.start()

        event_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **value
        }

        if self._is_online and self._producer:
            try:
                await self._producer.send_and_wait(topic, key=key, value=event_payload)
                self._total_published += 1
                return True
            except Exception as exc:
                logger.warning(f"Failed to deliver event to Kafka topic {topic}: {exc}. Buffering.")
                self._is_online = False

        # Fallback buffer
        self._fallback_buffer.append({
            "topic": topic,
            "key": key,
            "payload": event_payload,
            "buffered_at": datetime.now(timezone.utc).isoformat()
        })
        self._total_published += 1
        return True

    async def publish_interaction_async(
        self,
        user_id: str,
        anime_id: str,
        rating: float,
        interaction_type: str = "rating",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Asynchronously publish user rating or interaction to anime-interactions-stream."""
        event = {
            "event_type": "user_interaction",
            "user_id": str(user_id),
            "anime_id": str(anime_id),
            "rating": float(rating),
            "interaction_type": interaction_type,
            "metadata": metadata or {}
        }
        return await self.publish_raw(self.config.topic_interactions, key=str(user_id), value=event)

    async def publish_security_audit_async(
        self,
        event_type: str,
        prompt: str,
        risk_score: float,
        blocked: bool = False,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Asynchronously publish PyRIT red-team probe to security-audit-stream."""
        event = {
            "event_type": event_type,
            "prompt_snippet": prompt[:200] if prompt else "",
            "risk_score": float(risk_score),
            "blocked": bool(blocked),
            "details": details or {}
        }
        return await self.publish_raw(self.config.topic_security_audit, key=event_type, value=event)


    def publish_sync(self, topic: str, key: Optional[str], value: Dict[str, Any]) -> bool:
        """Synchronous wrapper to safely publish events from non-async code (Flask routes, scripts)."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.publish_raw(topic, key, value))
            return True
        except RuntimeError:
            # No running loop in current thread: use asyncio.run
            return asyncio.run(self.publish_raw(topic, key, value))

    # ── High-Level Domain Publishing Methods ───────────────────────────────────

    def publish_interaction(
        self,
        user_id: str,
        anime_id: str,
        rating: float,
        interaction_type: str = "rating",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish user rating or interaction to anime-interactions-stream.
        Keyed by user_id to ensure partitioned per-user sequential ordering.
        """
        event = {
            "event_type": "user_interaction",
            "user_id": str(user_id),
            "anime_id": str(anime_id),
            "rating": float(rating),
            "interaction_type": interaction_type,
            "metadata": metadata or {}
        }
        return self.publish_sync(self.config.topic_interactions, key=str(user_id), value=event)

    def publish_security_audit(
        self,
        event_type: str,
        prompt: str,
        risk_score: float,
        blocked: bool = False,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish PyRIT red-teaming or runtime guardrail violation to security-audit-stream.
        Keyed by event_type.
        """
        event = {
            "event_type": event_type,
            "prompt_snippet": prompt[:200] if prompt else "",
            "risk_score": float(risk_score),
            "blocked": bool(blocked),
            "details": details or {}
        }
        return self.publish_sync(self.config.topic_security_audit, key=event_type, value=event)

    def publish_research_event(
        self,
        query: str,
        status: str,
        dossier_id: Optional[str] = None,
        findings_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish LangGraph researcher progress event to agent-research-stream.
        Keyed by dossier_id or query hash.
        """
        key = dossier_id or str(hash(query))
        event = {
            "event_type": "agent_research_progress",
            "query": query,
            "status": status,
            "dossier_id": dossier_id,
            "findings_count": int(findings_count),
            "metadata": metadata or {}
        }
        return self.publish_sync(self.config.topic_agent_research, key=key, value=event)

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic health and metric status of the streaming producer."""
        return {
            "online": self._is_online,
            "bootstrap_servers": self.config.bootstrap_servers,
            "security_protocol": "SASL_SSL" if self.config.is_sasl_ssl else self.config.security_protocol,
            "buffer_depth": len(self._fallback_buffer),
            "total_events_handled": self._total_published,
            "topics": {
                "interactions": self.config.topic_interactions,
                "security_audit": self.config.topic_security_audit,
                "agent_research": self.config.topic_agent_research,
            }
        }

    def get_buffered_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recently buffered events for inspection or testing."""
        return list(self._fallback_buffer)[-limit:]


class KafkaStreamConsumer:
    """
    High-performance asynchronous consumer for streaming topics.
    Supports Kafka consumer groups for distributed scaling.
    """

    def __init__(self, topics: Optional[List[str]] = None, config: Optional[KafkaConfig] = None):
        self.config = config or KafkaConfig()
        self.topics = topics or [self.config.topic_interactions]
        self._consumer = None
        self._is_online = False

    async def start(self) -> bool:
        """Initialize consumer connection to assigned topics."""
        try:
            from aiokafka import AIOKafkaConsumer

            consumer_kwargs: Dict[str, Any] = {
                "bootstrap_servers": self.config.bootstrap_servers,
                "group_id": self.config.consumer_group,
                "auto_offset_reset": "earliest",
                "enable_auto_commit": True,
                "value_deserializer": lambda v: json.loads(v.decode("utf-8")),
                "key_deserializer": lambda k: k.decode("utf-8") if k else None,
                "request_timeout_ms": self.config.request_timeout_ms,
            }

            if self.config.is_sasl_ssl and self.config.sasl_password:
                ssl_context = ssl.create_default_context()
                consumer_kwargs.update({
                    "security_protocol": "SASL_SSL",
                    "sasl_mechanism": self.config.sasl_mechanism or "PLAIN",
                    "sasl_plain_username": self.config.sasl_username or "$ConnectionString",
                    "sasl_plain_password": self.config.sasl_password,
                    "ssl_context": ssl_context,
                })

            self._consumer = AIOKafkaConsumer(*self.topics, **consumer_kwargs)
            await asyncio.wait_for(self._consumer.start(), timeout=2.0)
            self._is_online = True
            logger.info(f"KafkaStreamConsumer connected to {self.topics} on {self.config.bootstrap_servers}")
            return True
        except Exception as exc:
            self._is_online = False
            if self._consumer:
                try:
                    await self._consumer.stop()
                except Exception:
                    pass
            self._consumer = None
            logger.warning(f"Consumer could not reach broker {self.config.bootstrap_servers} ({exc}). Running offline.")
            return False

    async def stop(self):
        """Safely disconnect consumer."""
        if self._consumer and self._is_online:
            try:
                await self._consumer.stop()
            except Exception as exc:
                logger.debug(f"Consumer stop error: {exc}")
            finally:
                self._consumer = None
                self._is_online = False

    async def fetch_batch(self, max_records: int = 10, timeout_ms: int = 1000) -> List[Dict[str, Any]]:
        """Fetch a batch of messages from subscribed topics."""
        if not self._is_online or not self._consumer:
            return []

        try:
            batch_result = await self._consumer.getmany(timeout_ms=timeout_ms, max_records=max_records)
            events = []
            for tp, records in batch_result.items():
                for record in records:
                    events.append({
                        "topic": record.topic,
                        "partition": record.partition,
                        "offset": record.offset,
                        "key": record.key,
                        "value": record.value,
                    })
            return events
        except Exception as exc:
            logger.error(f"Error fetching batch from Kafka: {exc}")
            return []


# Global singleton producer
_global_producer: Optional[KafkaStreamProducer] = None


def get_producer() -> KafkaStreamProducer:
    """Get or initialize the process-wide singleton Kafka stream producer."""
    global _global_producer
    if _global_producer is None:
        _global_producer = KafkaStreamProducer()
    return _global_producer
