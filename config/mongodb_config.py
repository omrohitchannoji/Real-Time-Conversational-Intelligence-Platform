import os
from dotenv import load_dotenv

load_dotenv(override=True)

MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI") or "mongodb://localhost:27017"
DATABASE_NAME = os.getenv("DATABASE_NAME", "context-modeling")

# Collection Names according to Architecture Specification
COLLECTION_MESSAGES = "messages"
COLLECTION_VALIDATION_ERRORS = "validation_errors"
COLLECTION_EMBEDDINGS = "embeddings"
COLLECTION_CONTEXTS = "contexts"
COLLECTION_RELATIONSHIPS = "relationships"
COLLECTION_USERS = "users"
COLLECTION_PROCESSING_LOGS = "processing_logs"
