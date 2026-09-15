import os
import sys
from pyspark.sql import SparkSession
from config.spark_config import APP_NAME, KAFKA_PACKAGE, SPARK_LOG_LEVEL

# 1. Set Python executable paths for PySpark Java Gateway worker processes
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# 2. Set HADOOP_HOME for PySpark Windows compatibility (winutils.exe)
if sys.platform.startswith("win"):
    hadoop_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hadoop"))
    os.environ["HADOOP_HOME"] = hadoop_dir
    os.environ["PATH"] += os.pathsep + os.path.join(hadoop_dir, "bin")

# 3. Dedicated local temp dir to prevent Windows AppData/Temp file lock errors
temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "spark_temp"))
os.makedirs(temp_dir, exist_ok=True)


def create_spark_session() -> SparkSession:
    """
    Creates and configures a PySpark SparkSession for Kafka streaming.
    """
    spark = (
        SparkSession.builder
        .appName(APP_NAME)
        .config("spark.jars.packages", KAFKA_PACKAGE)
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "2g")
        .config("spark.local.dir", temp_dir)
        .config("spark.sql.streaming.checkpointLocation", "./checkpoints")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel(SPARK_LOG_LEVEL)
    return spark