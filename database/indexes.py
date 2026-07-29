from database.mongo_connection import messages_col, validation_errors_col
from pymongo import ASCENDING


def setup_indexes():
    """
    Initializes collection indexes on MongoDB Atlas:
    Creates unique compound index on 'comment_id' in 'messages' collection
    to prevent duplicate message insertion on pipeline restart.
    """
    try:
        print("[INFO] Initializing MongoDB Indexes...")
        # Unique index on comment_id
        messages_col.create_index(
            [("comment_id", ASCENDING)],
            unique=True,
            name="idx_unique_comment_id"
        )
        print("[SUCCESS] MongoDB Indexes successfully created.")
    except Exception as e:
        print(f"[WARN] Index creation warning: {e}")


def clear_database_collections():
    """
    Clears all documents from messages and validation_errors collections
    to ensure a clean multi-domain baseline.
    """
    try:
        msg_result = messages_col.delete_many({})
        err_result = validation_errors_col.delete_many({})
        print(f"[CLEANUP] Deleted {msg_result.deleted_count} old documents from 'messages' collection.")
        print(f"[CLEANUP] Deleted {err_result.deleted_count} old documents from 'validation_errors' collection.")
    except Exception as e:
        print(f"[WARN] Cleanup error: {e}")


if __name__ == "__main__":
    setup_indexes()
    clear_database_collections()
