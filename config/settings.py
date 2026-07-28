import os
from dotenv import load_dotenv

load_dotenv()

# Kafka
BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVER")
TOPIC = os.getenv("KAFKA_TOPIC")

# Spark
APP_NAME = "RedditStreamingPipeline"
CHECKPOINT_LOCATION = "./checkpoints"

# Database (later)
DATABASE_URL = os.getenv("DATABASE_URL")

# FastAPI (later)
API_URL = os.getenv("API_URL")