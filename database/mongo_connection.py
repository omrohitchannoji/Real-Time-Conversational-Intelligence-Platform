from pymongo import MongoClient
from config.mongodb_config import (
    MONGO_URI,
    DATABASE_NAME,
    COLLECTION_MESSAGES,
    COLLECTION_VALIDATION_ERRORS,
    COLLECTION_EMBEDDINGS,
    COLLECTION_CONTEXTS,
    COLLECTION_RELATIONSHIPS,
    COLLECTION_USERS,
    COLLECTION_PROCESSING_LOGS
)

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# Collections initialization according to architecture specification
messages_col = db[COLLECTION_MESSAGES]
validation_errors_col = db[COLLECTION_VALIDATION_ERRORS]
embeddings_col = db[COLLECTION_EMBEDDINGS]
contexts_col = db[COLLECTION_CONTEXTS]
relationships_col = db[COLLECTION_RELATIONSHIPS]
users_col = db[COLLECTION_USERS]
processing_logs_col = db[COLLECTION_PROCESSING_LOGS]


def get_database():
    return db