"""
Unit and Integration Tests for Apache Kafka & Azure Event Hubs Streaming Layer.
"""

import json
import pytest
from src.streaming.kafka_stream import (
    KafkaConfig,
    KafkaStreamProducer,
    KafkaStreamConsumer,
    get_producer,
)
from application import app


def test_kafka_config_defaults():
    cfg = KafkaConfig()
    assert "localhost:9092" in cfg.bootstrap_servers or ":" in cfg.bootstrap_servers
    assert cfg.topic_interactions == "anime-interactions-stream"
    assert cfg.topic_security_audit == "security-audit-stream"
    assert cfg.topic_agent_research == "agent-research-stream"
    assert not cfg.is_sasl_ssl  # By default without password, plaintext


def test_kafka_config_sasl_ssl():
    cfg = KafkaConfig(
        bootstrap_servers="test-ns.servicebus.windows.net:9093",
        security_protocol="SASL_SSL",
        sasl_username="$ConnectionString",
        sasl_password="Endpoint=sb://test-ns...;",
    )
    assert cfg.is_sasl_ssl
    assert cfg.sasl_username == "$ConnectionString"


def test_producer_offline_buffering():
    # Configure an unreachable address to test graceful fallback
    cfg = KafkaConfig(bootstrap_servers="127.0.0.1:59999", request_timeout_ms=500)
    producer = KafkaStreamProducer(config=cfg)

    ok = producer.publish_interaction(
        user_id="user_test_99",
        anime_id="5114",
        rating=9.8,
        interaction_type="rating",
        metadata={"title": "FMA:B"}
    )
    assert ok is True

    status = producer.get_status()
    assert status["online"] is False
    assert status["buffer_depth"] >= 1
    assert status["total_events_handled"] >= 1

    events = producer.get_buffered_events(limit=5)
    assert len(events) >= 1
    last_event = events[-1]
    assert last_event["topic"] == "anime-interactions-stream"
    assert last_event["payload"]["user_id"] == "user_test_99"
    assert last_event["payload"]["rating"] == 9.8


def test_producer_security_and_research_publishing():
    cfg = KafkaConfig(bootstrap_servers="127.0.0.1:59999", request_timeout_ms=500)
    producer = KafkaStreamProducer(config=cfg)

    # Security audit event
    sec_ok = producer.publish_security_audit(
        event_type="test_pyrit_probe",
        prompt="system override test",
        risk_score=0.88,
        blocked=True,
        details={"attack": "override"}
    )
    assert sec_ok is True

    # Research event
    res_ok = producer.publish_research_event(
        query="Steins;Gate timeline theory",
        status="synthesized",
        dossier_id="dos_12345",
        findings_count=7
    )
    assert res_ok is True

    buffered = producer.get_buffered_events(limit=10)
    topics = [b["topic"] for b in buffered]
    assert "security-audit-stream" in topics
    assert "agent-research-stream" in topics


def test_consumer_offline_graceful_handling():
    async def _run():
        cfg = KafkaConfig(bootstrap_servers="127.0.0.1:59999", request_timeout_ms=500)
        consumer = KafkaStreamConsumer(topics=["anime-interactions-stream"], config=cfg)
        is_connected = await consumer.start()
        assert is_connected is False

        batch = await consumer.fetch_batch(max_records=5, timeout_ms=200)
        assert batch == []
        await consumer.stop()

    import asyncio
    asyncio.run(_run())


def test_flask_stream_status_endpoint():
    client = app.test_client()
    resp = client.get("/api/stream/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert "streaming" in data
    assert "topics" in data["streaming"]
    assert "interactions" in data["streaming"]["topics"]


def test_flask_stream_interaction_endpoint_success():
    client = app.test_client()
    payload = {
        "user_id": "test_user_777",
        "anime_id": "9253",
        "rating": 9.9,
        "interaction_type": "rating",
        "metadata": {"anime_title": "Steins;Gate"}
    }
    resp = client.post(
        "/api/stream/interaction",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "published"
    assert data["anime_id"] == "9253"
    assert data["user_id"] == "test_user_777"
    assert data["topic"] == "anime-interactions-stream"


def test_flask_stream_interaction_endpoint_validation():
    client = app.test_client()
    # Missing anime_id
    payload = {
        "user_id": "test_user_777",
        "rating": 9.9
    }
    resp = client.post(
        "/api/stream/interaction",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert "anime_id is required" in data["message"]
