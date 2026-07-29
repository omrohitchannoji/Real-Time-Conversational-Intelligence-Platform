import os
import csv
import time
from kafka import KafkaProducer
from config.kafka_config import PRODUCER_CONFIG, TOPIC
from kafka_pipeline.producer_validation import validate_and_serialize_record
from database.validation_logs import log_validation_errors

MULTI_DOMAIN_DATASET = os.path.join("datasets", "multi_domain_dataset.csv")
FALLBACK_DATASET = os.path.join("datasets", "streaming_dataset.csv")


def record_generator():
    """
    Multi-Domain CSV Comment Generator:
    Reads pre-harvested records across 10 subreddits from datasets/multi_domain_dataset.csv
    (technology, science, AskReddit, sports, gaming, space, movies, news, worldnews, geopolitics).
    """
    dataset_path = MULTI_DOMAIN_DATASET if os.path.exists(MULTI_DOMAIN_DATASET) else FALLBACK_DATASET
    print(f"[OFFLINE] Streaming 10-domain dataset from: '{dataset_path}'...")

    if not os.path.exists(dataset_path):
        print(f"[ERROR] No dataset file found at {dataset_path}.")
        return

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
    Streams multi-domain dataset records across 10 subreddits.
    Applies Layer 1 & 2 Pydantic validation, serializes to UTF-8 JSON bytes,
    and publishes to Kafka topic 'reddit_messages'.
    """
    print("=" * 60)
    print(f"[START] Launching Multi-Domain Kafka Producer (Target Topic: '{TOPIC}')")
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