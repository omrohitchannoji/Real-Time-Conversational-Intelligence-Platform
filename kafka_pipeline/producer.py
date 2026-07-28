import os
import csv
import time
from kafka import KafkaProducer
from config.kafka_config import PRODUCER_CONFIG, TOPIC
from kafka_pipeline.producer_validation import validate_and_serialize_record
from database.validation_logs import log_validation_errors

DATASET_PATH = os.path.join("datasets", "streaming_dataset.csv")


def start_producer(dataset_path: str = DATASET_PATH, delay_sec: float = 0.5):
    """
    Kafka Producer Application:
    Reads historical dataset rows, applies Layer 1 & 2 validation, serializes,
    and publishes to Kafka topic while routing failed records to DLQ.
    """
    print(f"[START] Starting Kafka Producer targeting topic: '{TOPIC}'...")
    
    # Initialize Kafka Producer with Layer 3 settings
    producer = KafkaProducer(**PRODUCER_CONFIG)

    if not os.path.exists(dataset_path):
        print(f"[WARN] Dataset file not found at {dataset_path}. Falling back to mock generator...")
        dataset_path = None

    def record_generator():
        if dataset_path:
            with open(dataset_path, mode="r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield {
                        "comment_id": row.get("comment_id"),
                        "parent_id": row.get("parent_id"),
                        "author": row.get("author"),
                        "created_utc": row.get("created_utc"),
                        "message": row.get("message"),
                        "source": row.get("subreddit", "reddit")
                    }
        else:
            import uuid
            import random
            from datetime import datetime
            authors = ["Alice", "Bob", "Charlie", "David", "Om"]
            messages = [
                "Real-time streaming pipeline test.",
                "SBERT embeddings generation coming soon.",
                "Context modeling and graph analysis.",
                "Testing invalid message filter test."
            ]
            while True:
                yield {
                    "comment_id": str(uuid.uuid4()),
                    "parent_id": None,
                    "author": random.choice(authors),
                    "created_utc": datetime.utcnow().isoformat(),
                    "message": random.choice(messages),
                    "source": "simulation"
                }

    sent_count = 0
    error_count = 0

    try:
        for record in record_generator():
            is_valid, payload_bytes, dlq_err = validate_and_serialize_record(record)
            
            if is_valid and payload_bytes:
                # Send bytes to Kafka topic
                producer.send(TOPIC, value=payload_bytes)
                sent_count += 1
                print(f"[SENT #{sent_count}] Comment ID: {record.get('comment_id')} | Author: {record.get('author')}")
            else:
                error_count += 1
                print(f"[REJECTED] Reason: {dlq_err.get('reason') if dlq_err else 'Unknown'}")
                if dlq_err:
                    log_validation_errors([dlq_err])

            producer.flush()
            time.sleep(delay_sec)

    except KeyboardInterrupt:
        print("\n[STOP] Producer manually stopped.")
    finally:
        producer.close()
        print(f"[SUMMARY] Sent {sent_count} valid records. Logged {error_count} validation errors to DLQ.")


if __name__ == "__main__":
    start_producer()