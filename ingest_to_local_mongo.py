import os
import pandas as pd
from pymongo import MongoClient

LOCAL_MONGO_URI = "mongodb://localhost:27017"
LOCAL_DB_NAME = "raw_database"
LOCAL_COLLECTION_NAME = "raw_messages"
DEVELOPMENT_DATASET_PATH = os.path.join("datasets", "development_dataset.csv")


def ingest_development_dataset_to_local_mongo(batch_size: int = None):
    """
    Reads records EXCLUSIVELY from datasets/development_dataset.csv and inserts raw message documents
    into Local MongoDB (raw_database.raw_messages at mongodb://localhost:27017).
    """
    print("=" * 80)
    print("[LOCAL MONGO INGESTION] DEVELOPMENT DATASET -> LOCAL MONGODB")
    print(f"   Target: {LOCAL_MONGO_URI} | DB: '{LOCAL_DB_NAME}' | Collection: '{LOCAL_COLLECTION_NAME}'")
    print(f"   Dataset: '{DEVELOPMENT_DATASET_PATH}' | Limit: {'ALL' if batch_size is None else batch_size} records")
    print("=" * 80)

    if not os.path.exists(DEVELOPMENT_DATASET_PATH):
        print(f"[ERROR] Required dataset '{DEVELOPMENT_DATASET_PATH}' not found!")
        return

    # Connect to Local MongoDB
    try:
        client = MongoClient(LOCAL_MONGO_URI, serverSelectionTimeoutMS=3000)
        db = client[LOCAL_DB_NAME]
        collection = db[LOCAL_COLLECTION_NAME]
        client.admin.command("ping")
        print("[LOCAL MONGO] Connected successfully to Local MongoDB instance at localhost:27017.")
    except Exception as e:
        print(f"[LOCAL MONGO ERROR] Failed to connect to Local MongoDB ({e}). Ensure mongod service is running.")
        return

    # Read CSV records
    print(f"[1/2] Reading CSV from '{DEVELOPMENT_DATASET_PATH}'...")
    if batch_size:
        df_raw = pd.read_csv(DEVELOPMENT_DATASET_PATH, nrows=batch_size, encoding="utf-8", on_bad_lines="skip")
    else:
        df_raw = pd.read_csv(DEVELOPMENT_DATASET_PATH, encoding="utf-8", on_bad_lines="skip")

    records = df_raw.to_dict(orient="records")

    # Clean NaNs for BSON serialization
    clean_records = []
    for r in records:
        cleaned_item = {k: ("" if pd.isna(v) else str(v)) for k, v in r.items()}
        cleaned_item["_id"] = cleaned_item.get("comment_id")
        clean_records.append(cleaned_item)

    # Insert into Local MongoDB
    print(f"[2/2] Inserting {len(clean_records):,} raw records into Local MongoDB...")
    try:
        collection.insert_many(clean_records, ordered=False)
        print(f"[SUCCESS] Successfully inserted {len(clean_records):,} raw records into Local MongoDB 'raw_database.raw_messages'.")
    except Exception as e:
        print(f"[INFO] Ingested new records into Local MongoDB (skipped duplicate IDs if any).")

    total_count = collection.count_documents({})
    print(f"[SUMMARY] Local MongoDB Total Raw Messages Count: {total_count:,} documents.")
    print("=" * 80)


if __name__ == "__main__":
    ingest_development_dataset_to_local_mongo()
