#!/usr/bin/env python3
"""
Kafka & Azure Event Hubs Streaming Consumer Demonstration
=========================================================
Demonstrates how downstream microservices consume stream events:
  - Online Recommender Worker: updates user embeddings and candidate sets
  - Security SIEM Worker: tracks PyRIT red-teaming alerts & threshold breaches
  - Dossier Indexer: indexes agent research dossiers in vector store

Usage:
  python scripts/kafka_consumer_demo.py --topic anime-interactions-stream
  python scripts/kafka_consumer_demo.py --topic security-audit-stream
  python scripts/kafka_consumer_demo.py --topic all
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.streaming.kafka_stream import KafkaStreamConsumer, KafkaConfig, get_producer


async def run_consumer_demo(topic: str, duration_sec: int = 10):
    print("=" * 70)
    print("HYBRID ANIME RECOMMENDER - KAFKA / AZURE EVENT HUBS CONSUMER DEMO")
    print("=" * 70)

    config = KafkaConfig()
    topics = [topic] if topic != "all" else [
        config.topic_interactions,
        config.topic_security_audit,
        config.topic_agent_research
    ]

    print(f"[*] Target Broker: {config.bootstrap_servers}")
    print(f"[*] Consumer Group: {config.consumer_group}")
    print(f"[*] Subscribed Topics: {', '.join(topics)}")
    print(f"[*] Listening for {duration_sec} seconds...")
    print("-" * 70)

    consumer = KafkaStreamConsumer(topics=topics, config=config)
    is_connected = await consumer.start()

    if not is_connected:
        print("\n[!] Live broker offline or unreachable.")
        print("[*] Reading from in-memory fallback buffer (offline demonstration):")
        producer = get_producer()
        events = producer.get_buffered_events(limit=10)
        if not events:
            # Produce mock events so consumer demonstration is immediately visible
            await producer.publish_interaction_async("user_demo_1", "5114", 9.5, "rating", {"name": "FMA: Brotherhood"})
            await producer.publish_security_audit_async("pyrit_probe", "Test jailbreak query", 0.91, True)
            events = producer.get_buffered_events(limit=10)

        for idx, ev in enumerate(events, 1):
            t = ev.get("topic")
            payload = ev.get("payload", {})
            etype = payload.get("event_type", "unknown")
            print(f"   [{idx}] [Buffer:{t}] Event: {etype} | Timestamp: {payload.get('timestamp')}")
            if etype == "user_interaction":
                print(f"       -> Recommender: Recalculating candidate pool for user={payload.get('user_id')} on anime={payload.get('anime_id')} (score={payload.get('rating')})")
            elif etype.startswith("pyrit") or etype == "security_audit":
                print(f"       -> SIEM Alert: High-risk prompt detected! Risk Score: {payload.get('risk_score')} (Blocked: {payload.get('blocked')})")
        print("\n[✔] Consumer demonstration completed successfully.")
        return

    # If live broker is connected
    try:
        end_time = asyncio.get_event_loop().time() + duration_sec
        msg_count = 0
        while asyncio.get_event_loop().time() < end_time:
            batch = await consumer.fetch_batch(max_records=5, timeout_ms=1000)
            for record in batch:
                msg_count += 1
                val = record.get("value", {})
                print(f"   [Live #{msg_count}] Topic: {record['topic']} | Key: {record['key']}")
                print(f"       -> Value: {val}")
            await asyncio.sleep(0.5)

        print(f"\n[✔] Live listening finished. Received {msg_count} stream events.")
    finally:
        await consumer.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consume stream events from Kafka")
    parser.add_argument("--topic", default="all", help="Topic to consume, or 'all'")
    parser.add_argument("--duration", type=int, default=5, help="Duration in seconds to listen")
    args = parser.parse_args()

    asyncio.run(run_consumer_demo(topic=args.topic, duration_sec=args.duration))
