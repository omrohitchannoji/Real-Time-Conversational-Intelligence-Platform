from pymongo.errors import BulkWriteError, DuplicateKeyError
from database.mongo_connection import messages_col


def insert_batch(records: list[dict]):
    """
    Inserts a micro-batch of clean, validated records into the 'messages' collection.
    Uses ordered=False so duplicate comment_ids are skipped gracefully without crashing.
    """
    if records:
        try:
            messages_col.insert_many(records, ordered=False)
        except (BulkWriteError, DuplicateKeyError) as e:
            # Duplicate keys are skipped gracefully; non-duplicate documents in batch still insert
            pass