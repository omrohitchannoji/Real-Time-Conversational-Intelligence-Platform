import os
from dotenv import load_dotenv

load_dotenv(override=True)

from kafka_pipeline.producer_validation import validate_and_serialize_record
from spark.consumer_validation import process_and_validate_record
from database.mongo_writer import insert_batch
from database.validation_logs import log_validation_errors
from database.mongo_connection import messages_col, validation_errors_col
import csv

DATASET_PATH = os.path.join("datasets", "streaming_dataset.csv")


def test_live_stream_to_atlas(num_records: int = 15):
    print("=" * 60)
    print("[START] STREAMING LIVE MESSAGES DIRECTLY TO MONGODB ATLAS")
    print("=" * 60)

    if not os.path.exists(DATASET_PATH):
        print(f"[FAILED] Dataset not found at {DATASET_PATH}")
        return

    valid_docs = []
    error_docs = []

    with open(DATASET_PATH, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if count >= num_records:
                break
            
            raw_doc = {
                "comment_id": row.get("comment_id"),
                "parent_id": row.get("parent_id"),
                "author": row.get("author"),
                "created_utc": row.get("created_utc"),
                "message": row.get("message"),
                "source": row.get("subreddit", "reddit")
            }

            # 1. Pre-Kafka Layer 1 & 2 Validation
            is_valid_producer, payload_bytes, producer_err = validate_and_serialize_record(raw_doc)
            
            if not is_valid_producer:
                if producer_err:
                    error_docs.append(producer_err)
                continue

            # 2. Consumer Layer 4-6 Validation & Layer 7 NLP Text Cleaning
            is_valid_consumer, clean_doc, consumer_err = process_and_validate_record(raw_doc)
            
            if is_valid_consumer and clean_doc:
                valid_docs.append(clean_doc)
                count += 1
                print(f"[VALIDATED #{count}] Comment ID: {clean_doc['comment_id']} | Author: {clean_doc['author']}")
                print(f"   Raw:   '{clean_doc['message_raw'][:60]}...'")
                print(f"   Clean: '{clean_doc['message'][:60]}...'")
            else:
                if consumer_err:
                    error_docs.append(consumer_err)

    # Insert valid documents into MongoDB Atlas 'messages'
    if valid_docs:
        insert_batch(valid_docs)
        print(f"\n[SUCCESS] Inserted {len(valid_docs)} clean documents into MongoDB Atlas 'messages' collection!")

    # Insert DLQ error documents if any
    if error_docs:
        log_validation_errors(error_docs)
        print(f"[WARN] Logged {len(error_docs)} rejected documents into MongoDB Atlas 'validation_errors' (DLQ).")

    # Fetch live count from Atlas
    atlas_msg_count = messages_col.count_documents({})
    atlas_err_count = validation_errors_col.count_documents({})

    print("\n" + "=" * 60)
    print("[METRICS] LIVE MONGODB ATLAS CLOUD DATABASE METRICS")
    print("=" * 60)
    print(f"  * Total Clean Messages in Atlas 'messages':          {atlas_msg_count}")
    print(f"  * Total DLQ Errors in Atlas 'validation_errors':     {atlas_err_count}")

    # Inspect first document in Atlas
    sample = messages_col.find_one({"comment_id": valid_docs[0]["comment_id"]}) if valid_docs else None
    if sample:
        print("\n[INSPECT] Sample Document Stored in MongoDB Atlas:")
        print(f"  * _id:          {sample.get('_id')}")
        print(f"  * comment_id:   {sample.get('comment_id')}")
        print(f"  * author:       {sample.get('author')}")
        print(f"  * message_raw:  {sample.get('message_raw')}")
        print(f"  * message:      {sample.get('message')}")
        print(f"  * created_utc:  {sample.get('created_utc')}")

    print("=" * 60)


if __name__ == "__main__":
    test_live_stream_to_atlas()
