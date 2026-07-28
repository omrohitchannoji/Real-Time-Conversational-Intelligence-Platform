from pyspark.sql.functions import col, from_json
from validation.schema_validation import SPARK_MESSAGE_SCHEMA


def extract_message(stream_df):
    """
    Parses raw Kafka byte payload into structured PySpark DataFrame columns.
    """
    json_df = stream_df.select(
        col("timestamp").alias("kafka_timestamp"),
        col("topic"),
        col("partition"),
        col("offset"),
        from_json(
            col("value").cast("string"),
            SPARK_MESSAGE_SCHEMA
        ).alias("data")
    )

    return json_df.select(
        "kafka_timestamp",
        "topic",
        "partition",
        "offset",
        "data.*"
    )