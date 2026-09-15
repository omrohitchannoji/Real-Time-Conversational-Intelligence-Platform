from config.kafka_config import BOOTSTRAP_SERVER, TOPIC


def read_kafka_stream(spark):
    """
    Reads streaming Dataframe from Apache Kafka topic.
    Caps maxOffsetsPerTrigger to 100 to prevent Java heap space OutOfMemory errors on large backlogs.
    """
    return (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", BOOTSTRAP_SERVER)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "earliest")
        .option("maxOffsetsPerTrigger", 100)
        .load()
    )