from concurrent.futures import ThreadPoolExecutor, as_completed
from database.mongo_writer import insert_batch
from database.validation_logs import log_validation_errors
from spark.consumer_validation import process_and_validate_record
from graph_db.neo4j_writer import Neo4jWriter

# One-Time Global Initialization of Neo4j Graph Driver
_global_neo4j_writer = Neo4jWriter()
try:
    _global_neo4j_writer.connect()
except Exception as e:
    print(f"[NEO4J INIT WARN] Neo4j graph driver connection notice: {e}")


def _process_single_row(row_dict: dict) -> tuple[bool, dict | None, dict | None]:
    """
    Worker task executed in parallel threads for each micro-batch row.
    """
    if "kafka_timestamp" in row_dict and row_dict["kafka_timestamp"]:
        row_dict["kafka_timestamp"] = str(row_dict["kafka_timestamp"])

    return process_and_validate_record(row_dict)


def _sync_to_neo4j_async(valid_records: list[dict]):
    """
    Asynchronously transforms and ingests micro-batch records into Neo4j Graph Database.
    Never blocks PySpark or MongoDB Atlas Cloud writes!
    """
    if not _global_neo4j_writer or not _global_neo4j_writer.is_connected:
        try:
            if not _global_neo4j_writer.connect():
                return
        except Exception:
            return

    neo4j_interactions = []
    for doc in valid_records:
        author_a = doc.get("author", "")
        author_b = doc.get("parent_author", "community_member")
        comment_id = doc.get("comment_id", "")
        parent_id = doc.get("parent_id", "")
        timestamp = doc.get("created_utc", "")
        
        ctx = doc.get("context_modeling", {})
        topic = ctx.get("detected_topic_name", "General Inquiries")

        if author_a:
            neo4j_interactions.append({
                "author_a": author_a,
                "author_b": author_b if author_b else "community_member",
                "comment_id": comment_id,
                "parent_id": parent_id,
                "timestamp": timestamp,
                "sentiment_score": 0.0,
                "relationship_score": 50.0,
                "topic": topic
            })

    if neo4j_interactions:
        try:
            count = _global_neo4j_writer.batch_write_interactions(neo4j_interactions)
            print(f"🕸️ [NEO4J GRAPH] Successfully ingested {count:,}/{len(neo4j_interactions):,} records into Neo4j Graph DB.")
        except Exception as e:
            print(f"[NEO4J WARN] Graph ingestion notice: {e}")


def write_to_mongodb(batch_df, batch_id):
    """
    Invoked by PySpark Structured Streaming foreachBatch for every micro-batch.
    Uses ThreadPoolExecutor (16 parallel workers) with live progress logging.
    Synchronizes clean records simultaneously to MongoDB Atlas Cloud & Neo4j Graph Database in real time.
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

    # 1. Write clean documents to MongoDB Atlas Cloud 'messages' & Neo4j Graph DB asynchronously
    if valid_records:
        try:
            insert_batch(valid_records)
            print(f"✅ [BATCH {batch_id}] Successfully inserted {len(valid_records):,} enriched records into MongoDB Atlas Cloud 'messages'.")
        except Exception as e:
            print(f"[WARN Batch {batch_id}] Primary insert message: {str(e)}")

        # Real-Time Neo4j Graph Sync (Non-blocking async execution)
        with ThreadPoolExecutor(max_workers=2) as async_pool:
            async_pool.submit(_sync_to_neo4j_async, valid_records)

    # 2. Write error documents to MongoDB Atlas Cloud 'validation_errors' (DLQ)
    if error_records:
        try:
            log_validation_errors(error_records)
            print(f"⚠️ [DLQ Batch {batch_id}] Logged {len(error_records)} rejected records into 'validation_errors'.")
        except Exception as e:
            print(f"[ERROR Batch {batch_id}] Error logging to DLQ: {str(e)}")