import os
import pyspark
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "RealTimeConversationalContextPipeline"
CHECKPOINT_LOCATION = os.getenv("SPARK_CHECKPOINT_DIR", "./checkpoints")
raw_ver = getattr(pyspark, "__version__", "3.5.5")
spark_ver = "3.5.5" if raw_ver.startswith("4") else raw_ver
KAFKA_PACKAGE = f"org.apache.spark:spark-sql-kafka-0-10_2.12:{spark_ver}"


SPARK_LOG_LEVEL = "ERROR"

