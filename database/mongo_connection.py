import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv(override=True)

# Cloud MongoDB Atlas Connection (Prioritizes MONGODB_URI or MONGO_ATLAS_URI from .env)
CLOUD_MONGO_URI = (
    os.getenv("MONGODB_URI") or 
    os.getenv("MONGO_ATLAS_URI") or 
    "mongodb+srv://omrohitchannoji7_db_user:NP8N1SBGSW9Q2XuA@context-modeling-cluste.maly4h1.mongodb.net"
)
DATABASE_NAME = os.getenv("DATABASE_NAME", "context-modeling")

# Local MongoDB Connection (Raw Messages Landing Store)
LOCAL_MONGO_URI = os.getenv("LOCAL_MONGO_URI", "mongodb://localhost:27017")
LOCAL_RAW_DB_NAME = "raw_database"

# Initialize Atlas Cloud Client (with timeout fallback for resilient network performance)
try:
    atlas_client = MongoClient(CLOUD_MONGO_URI, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)
    atlas_db = atlas_client[DATABASE_NAME]
    messages_col = atlas_db["messages"]
    validation_errors_col = atlas_db["validation_errors"]
    embeddings_col = atlas_db["embeddings"]
    contexts_col = atlas_db["contexts"]
    relationships_col = atlas_db["relationships"]
except Exception as e:
    print(f"[MONGO WARN] Atlas Cloud MongoDB connection note: {e}. Falling back to local MongoDB datastore.")
    try:
        local_fallback_client = MongoClient(LOCAL_MONGO_URI, serverSelectionTimeoutMS=2000)
        local_fallback_db = local_fallback_client["raw_database"]
        messages_col = local_fallback_db["raw_messages"]
        validation_errors_col = local_fallback_db["validation_errors"]
        embeddings_col = local_fallback_db["embeddings"]
        contexts_col = local_fallback_db["contexts"]
        relationships_col = local_fallback_db["relationships"]
    except Exception:
        messages_col = None
        validation_errors_col = None
        embeddings_col = None
        contexts_col = None
        relationships_col = None

# Initialize Local MongoDB Client (Raw Storage)
try:
    local_client = MongoClient(LOCAL_MONGO_URI, serverSelectionTimeoutMS=2000)
    local_raw_db = local_client[LOCAL_RAW_DB_NAME]
    raw_messages_col = local_raw_db["raw_messages"]
except Exception:
    raw_messages_col = None


def get_database():
    return atlas_db