import sys
from spark.spark_session import create_spark_session
from spark.kafka_reader import read_kafka_stream
from spark.transformations import extract_message
from spark.mongo_sink import write_to_mongodb


def main():
    print("[START] Initializing PySpark Structured Streaming Pipeline...")
    spark = create_spark_session()

    print("[CONNECT] Connecting to Kafka stream...")
    stream_df = read_kafka_stream(spark)

    print("[TRANSFORM] Parsing payload & applying schema transformations...")
    messages = extract_message(stream_df)

    import os
    checkpoint_dir = os.path.abspath("checkpoints/spark_consumer")
    os.makedirs(checkpoint_dir, exist_ok=True)

    print("[SINK] Starting micro-batch sink to MongoDB...")
    query = (
        messages.writeStream
        .foreachBatch(write_to_mongodb)
        .option("checkpointLocation", checkpoint_dir)
        .outputMode("append")
        .start()
    )

    print("[ACTIVE] Streaming engine active. Press Ctrl+C to terminate.")
    
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("\n[STOP] PySpark Streaming Consumer stopped by user.")
        try:
            query.stop()
            spark.stop()
        except Exception:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()