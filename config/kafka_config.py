import os
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVER", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "reddit_messages")

# Kafka Producer Reliability Settings (Layer 3 Validation)
PRODUCER_CONFIG = {
    "bootstrap_servers": BOOTSTRAP_SERVER,
    "acks": "all",
    "retries": 3,
    "max_in_flight_requests_per_connection": 1
}

CONSUMER_CONFIG = {
    "bootstrap_servers": BOOTSTRAP_SERVER,
    "auto_offset_reset": "earliest",
    "enable_auto_commit": True,
    "group_id": "context-modeling-group"
}
