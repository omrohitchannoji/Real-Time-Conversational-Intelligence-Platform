from database.mongo_writer import insert_batch
from database.validation_logs import log_validation_errors
from spark.consumer_validation import process_and_validate_record


def write_to_mongodb(batch_df, batch_id):
    """
    Invoked by Spark Structured Streaming foreachBatch for every micro-batch.
    Validates, cleans, and routes valid records to MongoDB 'messages' collection
    and invalid records to 'validation_errors' DLQ collection.
    """
    rows = batch_df.collect()
    if not rows:
        return

    valid_records = []
    error_records = []

    for row in rows:
        record = row.asDict(recursive=True)
        # Drop Spark-specific metadata fields if null
        if "kafka_timestamp" in record and record["kafka_timestamp"]:
            record["kafka_timestamp"] = str(record["kafka_timestamp"])

        is_valid, clean_doc, dlq_err = process_and_validate_record(record)
        if is_valid and clean_doc:
            valid_records.append(clean_doc)
        else:
            if dlq_err:
                error_records.append(dlq_err)

    # 1. Write clean documents to MongoDB 'messages'
    if valid_records:
        try:
            insert_batch(valid_records)
            print(f"[BATCH {batch_id}] Successfully inserted {len(valid_records)} clean records into 'messages'.")
        except Exception as e:
            print(f"[WARN Batch {batch_id}] Primary insert message: {str(e)}")

    # 2. Write error documents to MongoDB 'validation_errors' (DLQ)
    if error_records:
        try:
            log_validation_errors(error_records)
            print(f"[DLQ Batch {batch_id}] Logged {len(error_records)} rejected records into 'validation_errors'.")
        except Exception as e:
            print(f"[ERROR Batch {batch_id}] Error logging to DLQ: {str(e)}")