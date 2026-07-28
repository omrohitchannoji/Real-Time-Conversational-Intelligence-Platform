from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError
from database.mongo_connection import messages_col, validation_errors_col


def setup_indexes():
    """
    Creates necessary unique and performance indexes on MongoDB collections.
    Handles existing duplicate test documents gracefully.
    """
    print("[INFO] Initializing MongoDB Indexes...")

    # Delete sample test records if any exist
    messages_col.delete_many({"comment_id": "test001"})

    try:
        messages_col.create_index([("comment_id", ASCENDING)], unique=True, name="idx_unique_comment_id")
    except DuplicateKeyError:
        print("[WARN] Existing duplicate comment_ids found in MongoDB. Creating non-unique index for comment_id.")
        messages_col.create_index([("comment_id", ASCENDING)], name="idx_unique_comment_id")

    messages_col.create_index([("author", ASCENDING)], name="idx_author")
    messages_col.create_index([("created_utc", ASCENDING)], name="idx_created_utc")
    
    # Validation errors collection indexes
    validation_errors_col.create_index([("timestamp", ASCENDING)], name="idx_error_timestamp")
    validation_errors_col.create_index([("pipeline_stage", ASCENDING)], name="idx_error_stage")

    print("[SUCCESS] MongoDB Indexes successfully created.")


if __name__ == "__main__":
    setup_indexes()
