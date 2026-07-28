from config.kafka_config import BOOTSTRAP_SERVER, TOPIC


def read_kafka_stream(spark):
    """
    Reads streaming Dataframe from Apache Kafka topic.
    """
    return (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", BOOTSTRAP_SERVER)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )