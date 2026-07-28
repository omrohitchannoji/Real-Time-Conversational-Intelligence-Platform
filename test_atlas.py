import os
from dotenv import load_dotenv

# Load environment variables FIRST before importing database modules
load_dotenv(override=True)

from database.mongo_connection import get_database, messages_col, validation_errors_col
from database.indexes import setup_indexes


def test_atlas_connection():
    print("=" * 60)
    print("TESTING MONGODB ATLAS CONNECTION")
    print("=" * 60)
    
    mongo_uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI") or "mongodb://localhost:27017"
    db_name = os.getenv("DATABASE_NAME", "context-modeling")
    
    # Hide password in printed console string for security
    safe_uri = mongo_uri
    if "@" in mongo_uri:
        prefix, rest = mongo_uri.split("@", 1)
        safe_uri = "mongodb+srv://****:****@" + rest
        
    print(f"[CONFIG] Targeted Connection URI: {safe_uri}")
    print(f"[CONFIG] Targeted Database Name:  {db_name}")
    
    try:
        db = get_database()
        # Ping database server
        db.command('ping')
        print("[SUCCESS] Connection Test PASSED: Connected to MongoDB Atlas Cloud Server!")

        # Setup indexes on Atlas
        print("\n[INFO] Setting up collection indexes on Atlas...")
        setup_indexes()

        # Check existing collection statistics
        msg_count = messages_col.count_documents({})
        err_count = validation_errors_col.count_documents({})

        print("\n[STATS] Current Database Statistics:")
        print(f"  * Messages Collection Count:          {msg_count}")
        print(f"  * Validation Errors (DLQ) Count:      {err_count}")

        print("\n" + "=" * 60)
        print("MONGODB ATLAS IS READY FOR TEAM USE!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAILED] Connection Error: {str(e)}")
        print("\n[TIPS] Troubleshooting:")
        print("  1. Ensure 0.0.0.0/0 is active in MongoDB Atlas Network Access.")
        print("  2. Verify username and password in .env file.")


if __name__ == "__main__":
    test_atlas_connection()
