from concurrent.futures import ThreadPoolExecutor, as_completed
from database.mongo_writer import insert_batch
from database.validation_logs import log_validation_errors
from spark.consumer_validation import process_and_validate_record


def _process_single_row(row_dict: dict) -> tuple[bool, dict | None, dict | None]:
    """
    Worker task executed in parallel threads for each micro-batch row.
    """
    if "kafka_timestamp" in row_dict and row_dict["kafka_timestamp"]:
        row_dict["kafka_timestamp"] = str(row_dict["kafka_timestamp"])

    return process_and_validate_record(row_dict)


def write_to_mongodb(batch_df, batch_id):
    """
    Invoked by PySpark Structured Streaming foreachBatch for every micro-batch.
    Uses ThreadPoolExecutor (16 parallel workers) with live progress logging and 8s socket timeout protection.
    """
    rows = batch_df.collect()
    if not rows:
        return

    raw_records = [row.asDict(recursive=True) for row in rows]
    total_count = len(raw_records)
    print(f"\n[BATCH {batch_id}] Processing {total_count:,} records in parallel via ThreadPoolExecutor (16 Workers)...")

    valid_records = []
    error_records = []

    # Parallel worker execution (16 workers with live progress)
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(_process_single_row, rec) for rec in raw_records]
        
        completed_count = 0
        for future in as_completed(futures):
            completed_count += 1
            if completed_count % 100 == 0 or completed_count == total_count:
                print(f"      [BATCH {batch_id} PROGRESS] Processed {completed_count:,}/{total_count:,} records...", end="\r", flush=True)

            try:
                is_valid, clean_doc, dlq_err = future.result()
                if is_valid and clean_doc:
                    valid_records.append(clean_doc)
                elif dlq_err:
                    error_records.append(dlq_err)
            except Exception as e:
                pass

    print(f"\n[BATCH {batch_id}] Finished processing all {total_count:,} records!")

    # 1. Write clean documents to MongoDB Atlas Cloud 'messages'
    if valid_records:
        try:
            insert_batch(valid_records)
            print(f"✅ [BATCH {batch_id}] Successfully inserted {len(valid_records):,} enriched records into MongoDB Atlas Cloud 'messages'.")
        except Exception as e:
            print(f"[WARN Batch {batch_id}] Primary insert message: {str(e)}")

    # 2. Write error documents to MongoDB Atlas Cloud 'validation_errors' (DLQ)
    if error_records:
        try:
            log_validation_errors(error_records)
            print(f"⚠️ [DLQ Batch {batch_id}] Logged {len(error_records)} rejected records into 'validation_errors'.")
        except Exception as e:
            print(f"[ERROR Batch {batch_id}] Error logging to DLQ: {str(e)}")