import os
import json
from dotenv import load_dotenv

load_dotenv(override=True)

from kafka_pipeline.producer_validation import validate_and_serialize_record
from validation.parser import decode_utf8_bytes, parse_json_message
from spark.consumer_validation import process_and_validate_record
from database.mongo_writer import insert_batch
from database.validation_logs import log_validation_errors
from database.mongo_connection import messages_col, validation_errors_col, raw_messages_col
import csv

MULTI_DOMAIN_PATH = os.path.join("datasets", "multi_domain_dataset.csv")


def test_live_stream_to_atlas(num_records: int = 25):
    print("=" * 60)
    print("[START] STREAMING GENUINE MESSAGES DIRECTLY TO MONGODB ATLAS")
    print("=" * 60)

    records = []
    if raw_messages_col is not None:
        try:
            cursor = raw_messages_col.find({}).limit(num_records)
            for doc in cursor:
                records.append({
                    "comment_id": str(doc.get("comment_id")),
                    "parent_id": str(doc.get("parent_id")),
                    "author": str(doc.get("author")),
                    "created_utc": str(doc.get("created_utc")),
                    "message": str(doc.get("message")),
                    "source": str(doc.get("subreddit", "reddit"))
                })
        except Exception as e:
            print(f"[WARN] Local Mongo query error: {e}")

    if not records and os.path.exists(MULTI_DOMAIN_PATH):
        with open(MULTI_DOMAIN_PATH, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                records.append({
                    "comment_id": row.get("comment_id"),
                    "parent_id": row.get("parent_id"),
                    "author": row.get("author"),
                    "created_utc": row.get("created_utc"),
                    "message": row.get("message"),
                    "source": row.get("subreddit", "reddit")
                })
                if i >= num_records - 1:
                    break

    if not records:
        print("[FAILED] No records found in Local Mongo or CSV.")
        return

    validated_clean_docs = []
    dlq_error_records = []

    for idx, raw_record in enumerate(records, 1):
        # 1. Producer Validation (Layer 1 & 2)
        is_prod_valid, payload_bytes, prod_dlq = validate_and_serialize_record(raw_record)
        if not is_prod_valid:
            if prod_dlq:
                dlq_error_records.append(prod_dlq)
            continue

        # 2. Decode bytes to dict (Layer 4)
        is_dec_valid, dec_str, _ = decode_utf8_bytes(payload_bytes)
        is_json_valid, parsed_dict, _ = parse_json_message(dec_str)
        if not is_json_valid or not parsed_dict:
            continue

        # 3. Consumer Validation & Text Cleaning (Layer 5, 6, 7)
        is_cons_valid, clean_doc, cons_dlq = process_and_validate_record(parsed_dict)
        if is_cons_valid and clean_doc:
            validated_clean_docs.append(clean_doc)
            print(f"[VALIDATED #{idx}] Comment ID: {clean_doc['comment_id']} | Source: r/{clean_doc['source']} | Author: {clean_doc['author']}")
            print(f"   Raw:   '{raw_record['message'][:65]}...'")
            print(f"   Clean: '{clean_doc['message'][:65]}...'")
        else:
            if cons_dlq:
                dlq_error_records.append(cons_dlq)

    # 4. Write Validated Clean Batch to MongoDB Atlas Cloud 'messages' collection
    if validated_clean_docs:
        inserted_count = insert_batch(validated_clean_docs)
        print(f"\n[SUCCESS] Inserted {inserted_count} genuine clean documents into MongoDB Atlas 'messages' collection!")

    # 5. Log DLQ errors to Atlas 'validation_errors'
    if dlq_error_records:
        log_validation_errors(dlq_error_records)

    # 6. Output Database Metrics
    print("\n" + "=" * 60)
    print("[METRICS] LIVE MONGODB ATLAS CLOUD DATABASE METRICS")
    print("=" * 60)
    print(f"  * Total Clean Messages in Atlas 'messages':          {messages_col.count_documents({})}")
    print(f"  * Total DLQ Errors in Atlas 'validation_errors':     {validation_errors_col.count_documents({})}")

    sample_doc = messages_col.find_one({})
    if sample_doc:
        print("\n[INSPECT] Sample Document Stored in MongoDB Atlas:")
        print(f"  * _id:          {sample_doc.get('_id')}")
        print(f"  * comment_id:   {sample_doc.get('comment_id')}")
        print(f"  * author:       {sample_doc.get('author')}")
        print(f"  * source:       r/{sample_doc.get('source')}")
        print(f"  * message:      {sample_doc.get('message')}")
        print(f"  * created_utc:  {sample_doc.get('created_utc')}")
    print("=" * 60)


if __name__ == "__main__":
    test_live_stream_to_atlas(num_records=25)
