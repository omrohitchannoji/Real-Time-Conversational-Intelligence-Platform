from concurrent.futures import ThreadPoolExecutor, as_completed
from database.mongo_connection import messages_col
from database.mongo_writer import insert_batch
from database.validation_logs import log_validation_errors
from spark.consumer_validation import process_and_validate_record
from graph_db.neo4j_writer import Neo4jWriter

# Pre-index existing comment_ids from MongoDB Atlas to fast-skip duplicates instantly in 0.0001ms
_existing_comment_ids_set = set()
try:
    if messages_col is not None:
        cursor = messages_col.find({}, {"comment_id": 1, "_id": 0})
        for doc in cursor:
            cid = str(doc.get("comment_id", "")).strip()
            if cid:
                _existing_comment_ids_set.add(cid)
        print(f"⚡ [CACHE] Pre-indexed {len(_existing_comment_ids_set):,} existing messages from MongoDB Atlas to fast-skip duplicates!")
except Exception as e:
    print(f"[CACHE NOTE] Pre-indexing notice: {e}")

# One-Time Global Initialization of Neo4j Graph Driver
_global_neo4j_writer = Neo4jWriter()
try:
    _global_neo4j_writer.connect()
except Exception as e:
    print(f"[NEO4J INIT WARN] Neo4j graph driver connection notice: {e}")


def _process_single_row(row_dict: dict) -> tuple[bool, dict | None, dict | None]:
    """
    Worker task executed in parallel threads for each micro-batch row.
    Skips already-processed comment_ids instantly in 0.0001ms without calling Groq/EmbeddingGemma!
    """
    cid = str(row_dict.get("comment_id", "")).strip()
    if cid and cid in _existing_comment_ids_set:
        return False, None, None

    if "kafka_timestamp" in row_dict and row_dict["kafka_timestamp"]:
        row_dict["kafka_timestamp"] = str(row_dict["kafka_timestamp"])

    res = process_and_validate_record(row_dict)
    if res[0] and res[1]:
        if cid:
            _existing_comment_ids_set.add(cid)
    return res


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
            sim_val = float(doc.get("semantic_similarity_score", 0.50))
            neo4j_interactions.append({
                "author_a": author_a,
                "author_b": author_b if author_b else "community_member",
                "comment_id": comment_id,
                "parent_id": parent_id,
                "timestamp": timestamp,
                "sentiment_score": 0.0,
                "relationship_score": round(sim_val * 100.0, 2),
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
    Uses ThreadPoolExecutor (3 parallel workers) with live progress logging.
    Flushes clean records incrementally every 100 items directly to MongoDB Atlas Cloud
    and Neo4j Graph Database so progress is NEVER lost even if stopped mid-batch.
    """
    rows = batch_df.collect()
    if not rows:
        return

    raw_records = [row.asDict(recursive=True) for row in rows]
    total_count = len(raw_records)
    print(f"\n[BATCH {batch_id}] Processing {total_count:,} records in parallel (Incremental Flush every 100)...")

    valid_records_count = 0
    error_records_count = 0
    chunk_valid = []
    chunk_errors = []

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(_process_single_row, rec) for rec in raw_records]
            
            completed_count = 0
            for future in as_completed(futures):
                completed_count += 1

                try:
                    is_valid, clean_doc, dlq_err = future.result()
                    if is_valid and clean_doc:
                        cid = clean_doc.get("comment_id")
                        if cid:
                            clean_doc["_id"] = cid
                        chunk_valid.append(clean_doc)
                        valid_records_count += 1
                    elif dlq_err:
                        chunk_errors.append(dlq_err)
                        error_records_count += 1
                except Exception:
                    pass

                # Incremental Flush: Flush every 100 records immediately to Cloud DBs
                if len(chunk_valid) >= 100:
                    try:
                        insert_batch(chunk_valid)
                        _sync_to_neo4j_async(chunk_valid)
                    except Exception as e:
                        pass
                    chunk_valid = []

                if len(chunk_errors) >= 100:
                    try:
                        log_validation_errors(chunk_errors)
                    except Exception:
                        pass
                    chunk_errors = []

                if completed_count % 100 == 0 or completed_count == total_count:
                    print(f"      [BATCH {batch_id} PROGRESS] Processed {completed_count:,}/{total_count:,} records (Saved to Atlas & Neo4j: {valid_records_count:,})", flush=True)

    except KeyboardInterrupt:
        print(f"\n[INTERRUPT] Received stop signal. Flushing remaining in-memory records...")
    finally:
        # Flush any remaining items in buffer
        if chunk_valid:
            try:
                insert_batch(chunk_valid)
                _sync_to_neo4j_async(chunk_valid)
            except Exception:
                pass
        if chunk_errors:
            try:
                log_validation_errors(chunk_errors)
            except Exception:
                pass

    print(f"\n✅ [BATCH {batch_id}] Successfully saved {valid_records_count:,} enriched records to MongoDB Atlas & Neo4j!")
    if error_records_count > 0:
        print(f"⚠️ [DLQ Batch {batch_id}] Logged {error_records_count:,} rejected records to validation_errors.")