import os
import csv
import time
from kafka import KafkaProducer
from config.kafka_config import PRODUCER_CONFIG, TOPIC
from kafka_pipeline.producer_validation import validate_and_serialize_record
from database.validation_logs import log_validation_errors
from database.mongo_connection import raw_messages_col

MULTI_DOMAIN_DATASET = os.path.join("datasets", "multi_domain_dataset.csv")


def record_generator():
    """
    DB-to-DB Raw Message Generator:
    Queries raw, unvalidated messages from Local MongoDB 'raw_messages' collection.
    Falls back to datasets/multi_domain_dataset.csv if Local Mongo is unavailable.
    """
    if raw_messages_col is not None:
        try:
            print("[PRODUCER] Querying raw records from Local MongoDB 'raw_database.raw_messages'...")
            cursor = raw_messages_col.find({"status": "UNPROCESSED"})
            count = 0
            for doc in cursor:
                count += 1
                yield {
                    "comment_id": doc.get("comment_id"),
                    "parent_id": doc.get("parent_id"),
                    "author": doc.get("author"),
                    "created_utc": doc.get("created_utc"),
                    "message": doc.get("message"),
                    "source": doc.get("subreddit", "reddit")
                }
            if count > 0:
                return
        except Exception as e:
            print(f"[WARN] Could not read from Local MongoDB ({e}). Falling back to CSV file...")

    # Fallback CSV generator
    dataset_path = MULTI_DOMAIN_DATASET
    print(f"[PRODUCER] Streaming from CSV file: '{dataset_path}'...")
    if os.path.exists(dataset_path):
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


def start_producer(delay_sec: float = 0.5):
    """
    Kafka Producer Application:
    Streams raw records from Local MongoDB / CSV across 10 subreddits.
    Applies Layer 1 & 2 Pydantic validation, serializes to UTF-8 JSON bytes,
    and publishes to Kafka topic 'reddit_messages'.
    """
    print("=" * 60)
    print(f"[START] Launching Enterprise DB-Driven Kafka Producer (Topic: '{TOPIC}')")
    print("=" * 60)

    # Initialize Kafka Producer with Layer 3 transport config (acks='all', retries=3)
    producer = KafkaProducer(**PRODUCER_CONFIG)

    sent_count = 0
    error_records = []

    try:
        for raw_record in record_generator():
            # Apply Layer 1 Pydantic Validation & Layer 2 Serialization Validation
            is_valid, payload_bytes, dlq_err = validate_and_serialize_record(raw_record)

            if is_valid and payload_bytes:
                producer.send(TOPIC, value=payload_bytes)
                sent_count += 1
                source_tag = raw_record.get("source", "reddit")
                print(f"[PRODUCED #{sent_count}] Topic: {TOPIC} | Source: r/{source_tag} | Comment ID: {raw_record['comment_id']}")
                time.sleep(delay_sec)
            else:
                if dlq_err:
                    error_records.append(dlq_err)
                    print(f"[REJECTED] {dlq_err['reason']} -> DLQ")

            # Periodically flush DLQ error logs
            if len(error_records) >= 10:
                log_validation_errors(error_records)
                error_records.clear()

    except KeyboardInterrupt:
        print("\n[STOP] Producer execution paused by user.")
    finally:
        if error_records:
            log_validation_errors(error_records)
        producer.flush()
        producer.close()
        print(f"[FINISHED] Total records published to Kafka: {sent_count}")


if __name__ == "__main__":
    start_producer()