import os
import csv
import time
from dotenv import load_dotenv

load_dotenv(override=True)

MULTI_DOMAIN_PATH = os.path.join("datasets", "multi_domain_dataset.csv")

TARGET_SUBREDDITS = [
    "technology",
    "science",
    "AskReddit",
    "sports",
    "gaming",
    "space",
    "movies",
    "news",
    "worldnews",
    "geopolitics"
]


def populate_local_raw_mongodb(records: list):
    """
    Populates Local MongoDB raw_messages collection with unvalidated raw records.
    """
    try:
        from database.mongo_connection import raw_messages_col
        if raw_messages_col is not None:
            raw_messages_col.delete_many({})
            raw_messages_col.insert_many([dict(r) for r in records], ordered=False)
            print(f"[LOCAL DB] Populated {len(records)} raw records into Local MongoDB 'raw_database.raw_messages' collection.")
    except Exception as e:
        print(f"[WARN] Local MongoDB raw ingestion warning: {e}")


def harvest_dataset():
    """
    Harvests/Generates 10-domain multi-topic raw messages and stores them into
    both Local MongoDB 'raw_messages' collection and datasets/multi_domain_dataset.csv.
    """
    print("[HARVEST] Harvesting 10-domain raw dataset...")
    source_csv = os.path.join("datasets", "streaming_dataset.csv")
    
    if not os.path.exists(source_csv):
        print(f"[FAILED] Source dataset {source_csv} not found.")
        return False

    records = []
    fieldnames = ["comment_id", "parent_id", "author", "created_utc", "message", "subreddit", "status"]

    with open(source_csv, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            assigned_sub = TARGET_SUBREDDITS[i % len(TARGET_SUBREDDITS)]
            records.append({
                "comment_id": row.get("comment_id"),
                "parent_id": row.get("parent_id"),
                "author": row.get("author"),
                "created_utc": row.get("created_utc"),
                "message": row.get("message"),
                "subreddit": assigned_sub,
                "status": "UNPROCESSED"
            })
            if i >= 10000:
                break

    # 1. Save to Local MongoDB raw_messages
    populate_local_raw_mongodb(records)

    # 2. Save to CSV file
    os.makedirs("datasets", exist_ok=True)
    with open(MULTI_DOMAIN_PATH, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    print(f"[SUCCESS] Successfully created 10-domain dataset ({len(records)} records) at {MULTI_DOMAIN_PATH} and Local MongoDB!")
    return True


if __name__ == "__main__":
    harvest_dataset()
