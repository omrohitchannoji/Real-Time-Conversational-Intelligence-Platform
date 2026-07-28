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

    print("[SINK] Starting micro-batch sink to MongoDB...")
    query = (
        messages.writeStream
        .foreachBatch(write_to_mongodb)
        .outputMode("append")
        .start()
    )

    print("[ACTIVE] Streaming engine active. Press Ctrl+C to terminate.")
    query.awaitTermination()


if __name__ == "__main__":
    main()