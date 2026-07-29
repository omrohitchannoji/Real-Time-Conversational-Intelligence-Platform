import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv(override=True)

# Cloud MongoDB Atlas Connection (Clean Source of Truth)
CLOUD_MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI") or "mongodb://localhost:27017"
DATABASE_NAME = os.getenv("DATABASE_NAME", "context-modeling")

# Local MongoDB Connection (Raw Messages Landing Store)
LOCAL_MONGO_URI = os.getenv("LOCAL_MONGO_URI", "mongodb://localhost:27017")
LOCAL_RAW_DB_NAME = "raw_database"

# Initialize Atlas Cloud Client
atlas_client = MongoClient(CLOUD_MONGO_URI)
atlas_db = atlas_client[DATABASE_NAME]

# Atlas Collections
messages_col = atlas_db["messages"]
validation_errors_col = atlas_db["validation_errors"]
embeddings_col = atlas_db["embeddings"]
contexts_col = atlas_db["contexts"]
relationships_col = atlas_db["relationships"]

# Initialize Local MongoDB Client (Raw Storage)
try:
    local_client = MongoClient(LOCAL_MONGO_URI, serverSelectionTimeoutMS=2000)
    local_raw_db = local_client[LOCAL_RAW_DB_NAME]
    raw_messages_col = local_raw_db["raw_messages"]
except Exception:
    raw_messages_col = None


def get_database():
    return atlas_db