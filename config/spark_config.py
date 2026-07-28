import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "RealTimeConversationalContextPipeline"
CHECKPOINT_LOCATION = os.getenv("SPARK_CHECKPOINT_DIR", "./checkpoints")
KAFKA_PACKAGE = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5"

SPARK_LOG_LEVEL = "ERROR"
