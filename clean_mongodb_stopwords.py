import sys
import os
import re

# Auto-resolve project root directory in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.mongo_connection import messages_col
from dashboard.analytics import STOPWORDS
from pymongo import UpdateOne


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def clean_stopwords_in_mongodb():
    """
    Performs a batch database migration on MongoDB Atlas:
    Iterates through all documents in the 'messages' collection and removes
    stop words & generic filler terms directly from 'context_modeling.topic_keywords'.
    """
    print("=" * 70)
    print("[MIGRATION] MONGODB ATLAS STOPWORDS CLEANUP")
    print("=" * 70)

    try:
        query = {"context_modeling.topic_keywords": {"$exists": True, "$ne": []}}
        total_docs = messages_col.count_documents(query)
        print(f"[INFO] Found {total_docs:,} documents in MongoDB Atlas with 'topic_keywords'.")

        if total_docs == 0:
            print("[INFO] No documents to update.")
            return

        cursor = messages_col.find(query, {"_id": 1, "context_modeling.topic_keywords": 1})

        bulk_operations = []
        modified_count = 0
        total_words_removed = 0
        processed = 0

        for doc in cursor:
            processed += 1
            doc_id = doc["_id"]
            kws = doc.get("context_modeling", {}).get("topic_keywords", [])

            if not isinstance(kws, list):
                continue

            cleaned_kws = []
            for k in kws:
                k_str = str(k).strip()
                cleaned_k = re.sub(r'[^\w\s]', '', k_str).lower().strip()
                if k_str and len(k_str) > 2 and cleaned_k not in STOPWORDS:
                    cleaned_kws.append(k_str.title())

            if len(cleaned_kws) != len(kws) or cleaned_kws != kws:
                words_removed = len(kws) - len(cleaned_kws)
                total_words_removed += words_removed
                modified_count += 1
                bulk_operations.append(
                    UpdateOne(
                        {"_id": doc_id},
                        {"$set": {"context_modeling.topic_keywords": cleaned_kws}}
                    )
                )

            # Execute bulk writes in batches of 500
            if len(bulk_operations) >= 500:
                messages_col.bulk_write(bulk_operations, ordered=False)
                print(f"  --> Executed bulk update batch... (Processed {processed}/{total_docs} documents)")
                bulk_operations = []

        # Flush remaining bulk operations
        if bulk_operations:
            messages_col.bulk_write(bulk_operations, ordered=False)

        print("-" * 70)
        print(f"[SUCCESS] MIGRATION COMPLETED SUCCESSFULLY!")
        print(f"  * Total Documents Scanned:  {processed:,}")
        print(f"  * Documents Updated in DB:  {modified_count:,}")
        print(f"  * Stop Words Removed in DB: {total_words_removed:,}")
        print("=" * 70)

    except Exception as e:
        print(f"[ERROR] Error performing MongoDB cleanup migration: {e}")


if __name__ == "__main__":
    clean_stopwords_in_mongodb()
