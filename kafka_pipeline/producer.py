import os
import time
import pymongo
from kafka import KafkaProducer
from config.kafka_config import PRODUCER_CONFIG, TOPIC
from kafka_pipeline.producer_validation import validate_and_serialize_record
from database.validation_logs import log_validation_errors

LOCAL_MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
LOCAL_DB_NAME = "raw_database"
LOCAL_COLLECTION_NAME = "raw_messages"


def record_generator():
    """
    Local MongoDB Raw Message Generator:
    Streams raw message documents directly from Local MongoDB (raw_database.raw_messages).
    Zero CSV dependency!
    """
    print(f"[PRODUCER] Querying raw message records from Local MongoDB ({LOCAL_MONGO_URI} [{LOCAL_DB_NAME}.{LOCAL_COLLECTION_NAME}])...")
    try:
        client = pymongo.MongoClient(LOCAL_MONGO_URI, serverSelectionTimeoutMS=5000)
        col = client[LOCAL_DB_NAME][LOCAL_COLLECTION_NAME]
        cursor = col.find({}, {"_id": 0})
        
        count = 0
        for doc in cursor:
            count += 1
            yield {
                "comment_id": doc.get("comment_id", f"c_{count}"),
                "parent_id": doc.get("parent_id", ""),
                "author": doc.get("author", "anonymous"),
                "created_utc": doc.get("created_utc", ""),
                "message": doc.get("message", doc.get("text", "")),
                "source": "local_mongodb_raw_database"
            }
        print(f"[PRODUCER] Total raw documents yielded from Local MongoDB: {count:,}")
    except Exception as e:
        print(f"[PRODUCER ERROR] Failed to fetch records from Local MongoDB ({e})!")
        return


def start_producer(delay_sec: float = 0.02):
    """
    Kafka Producer Application:
    Streams raw messages directly from Local MongoDB (raw_database.raw_messages).
    Applies Layer 1 Pydantic validation, serializes to UTF-8 JSON bytes,
    and publishes to Kafka topic 'reddit_messages'.
    """
    print("=" * 60)
    print(f"[START] Launching Local MongoDB Kafka Producer (Topic: '{TOPIC}')")
    print("=" * 60)

    producer = KafkaProducer(**PRODUCER_CONFIG)

    sent_count = 0
    error_records = []

    try:
        for raw_record in record_generator():
            is_valid, payload_bytes, dlq_err = validate_and_serialize_record(raw_record)

            if is_valid and payload_bytes:
                producer.send(TOPIC, value=payload_bytes)
                sent_count += 1
                if sent_count % 500 == 0:
                    print(f"[PRODUCED #{sent_count:,}] Topic: {TOPIC} | Comment ID: {raw_record['comment_id']}")
                if delay_sec > 0:
                    time.sleep(delay_sec)
            else:
                if dlq_err:
                    error_records.append(dlq_err)
                    print(f"[REJECTED] {dlq_err['reason']} -> DLQ")

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
        print(f"[FINISHED] Total records published to Kafka from Local Mongo: {sent_count:,}")


if __name__ == "__main__":
    start_producer(delay_sec=0.02)