"""
Real-time Event Streaming Layer for Hybrid Anime Recommender & AI Security.
Supports Apache Kafka, AWS MSK, and Azure Event Hubs (Kafka 1.0+ surface).
"""

from src.streaming.kafka_stream import (
    KafkaConfig,
    KafkaStreamProducer,
    KafkaStreamConsumer,
    get_producer,
)

__all__ = [
    "KafkaConfig",
    "KafkaStreamProducer",
    "KafkaStreamConsumer",
    "get_producer",
]
