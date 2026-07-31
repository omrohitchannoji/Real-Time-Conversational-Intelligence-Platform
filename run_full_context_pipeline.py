import os
import pymongo
from dotenv import load_dotenv
from nlp.cleaner import clean_text
from nlp.embeddings import EmbeddingGemmaEmbedder
from nlp.vector_store import ConversationalVectorStore
from nlp.topic_detection import GroqLLMTopicDetector

load_dotenv(override=True)

LOCAL_MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
LOCAL_DB = "raw_database"
LOCAL_COLLECTION = "raw_messages"

# Reads MONGODB_URI or MONGO_ATLAS_URI from .env
ATLAS_MONGO_URI = os.getenv("MONGODB_URI", os.getenv("MONGO_ATLAS_URI", ""))
ATLAS_DB = "context-modeling"
ATLAS_COLLECTION = "messages"


def run_full_end_to_end_pipeline(batch_limit: int = 100):
    """
    MASTER END-TO-END PIPELINE:
    1. Fetches raw messages from Local MongoDB (raw_database.raw_messages).
    2. Cleans message text via nlp/cleaner.py.
    3. Generates 768D google/embeddinggemma-300m Vectors via nlp/embeddings.py.
    4. Indexes vectors in ChromaDB Vector Database (nlp/vector_store.py).
    5. Classifies Human-Grade Topic Categories & Intent via Groq LLM (nlp/topic_detection.py).
    6. Stores Enriched Message Documents in MongoDB Atlas Cloud (context-modeling.messages).
    """
    print("=" * 85)
    print("[MASTER PIPELINE] LOCAL MONGO -> CLEANER -> EMBEDDINGGEMMA -> CHROMADB -> GROQ LLM -> ATLAS CLOUD")
    print(f"   Local Source: {LOCAL_MONGO_URI} [{LOCAL_DB}.{LOCAL_COLLECTION}]")
    print(f"   Cloud Target: MongoDB Atlas Cloud [{ATLAS_DB}.{ATLAS_COLLECTION}]")
    print(f"   Batch Limit:  {batch_limit} records")
    print("=" * 85)

    # Connect to Local MongoDB
    try:
        local_client = pymongo.MongoClient(LOCAL_MONGO_URI, serverSelectionTimeoutMS=5000)
        local_col = local_client[LOCAL_DB][LOCAL_COLLECTION]
        raw_docs = list(local_col.find().limit(batch_limit))
        print(f"\n[1/5] Fetched {len(raw_docs)} raw message records from Local MongoDB.")
    except Exception as e:
        print(f"[ERROR] Could not connect to Local MongoDB ({LOCAL_MONGO_URI}): {e}")
        return

    if not raw_docs:
        print("[WARN] Local MongoDB collection is empty. Run ingest_to_local_mongo.py first!")
        return

    # Connect to MongoDB Atlas Cloud
    atlas_col = None
    if ATLAS_MONGO_URI and "mongodb+srv" in ATLAS_MONGO_URI:
        try:
            atlas_client = pymongo.MongoClient(ATLAS_MONGO_URI, serverSelectionTimeoutMS=10000)
            atlas_col = atlas_client[ATLAS_DB][ATLAS_COLLECTION]
            print(f"[ATLAS CLOUD] Connected to MongoDB Atlas Cloud collection '{ATLAS_DB}.{ATLAS_COLLECTION}'.")
        except Exception as e:
            print(f"[ATLAS CLOUD WARN] Could not connect to MongoDB Atlas Cloud ({e}).")

    # Initialize Embedding Engine & ChromaDB Vector DB
    print(f"\n[2/5] Initializing 768D google/embeddinggemma-300m Embeddings & ChromaDB...")
    vstore = ConversationalVectorStore(collection_name="atlas_enriched_context_store")
    
    # Initialize Groq LLM Context Detector
    print(f"\n[3/5] Initializing Groq LPU LLM Engine (llama-3.3-70b-versatile)...")
    llm_detector = GroqLLMTopicDetector()

    # Step 4: Process Each Message Sequential Pipeline
    print(f"\n[4/5] Processing {len(raw_docs)} messages through Master End-to-End Pipeline...")
    enriched_documents = []

    for idx, doc in enumerate(raw_docs):
        msg_id = str(doc.get("comment_id", doc.get("_id", f"c_{idx}")))
        author = str(doc.get("author", "anonymous"))
        raw_text = str(doc.get("message", doc.get("text", "")))

        if not raw_text.strip() or raw_text.strip() in ["[deleted]", "[removed]"]:
            continue

        # 4a. Clean text
        cleaned_text = clean_text(raw_text)

        # 4b. Generate 768D embedding vector
        embedding_vec = vstore.embedder.get_embedding(cleaned_text)

        # 4c. LLM Context & Topic Classification
        llm_result = llm_detector.detect_topic(cleaned_text)

        # Build enriched document schema
        enriched_doc = {
          "comment_id": msg_id,
          "author": author,
          "raw_message": raw_text,
          "cleaned_message": cleaned_text,
          "context_modeling": {
            "detected_topic_name": llm_result["detected_topic_name"],
            "topic_keywords": llm_result["topic_keywords"],
            "summary_intent": llm_result["summary_intent"],
            "vector_embedding_dim": len(embedding_vec),
            "indexed_in_chromadb": True
          }
        }
        enriched_documents.append(enriched_doc)

        # Index in ChromaDB Vector Database
        vstore.collection.add(
            ids=[msg_id],
            documents=[cleaned_text],
            embeddings=[embedding_vec],
            metadatas=[{"author": author, "topic": llm_result["detected_topic_name"]}]
        )

        if (idx + 1) % 10 == 0 or (idx + 1) == len(raw_docs):
            print(f"      Pipeline processed {idx + 1}/{len(raw_docs)} messages...")

    # Step 5: Save Enriched Documents to MongoDB Atlas Cloud
    print(f"\n[5/5] Upserting {len(enriched_documents)} enriched context documents into MongoDB Atlas Cloud...")
    if atlas_col is not None:
        success_count = 0
        for edoc in enriched_documents:
            try:
                atlas_col.update_one(
                    {"comment_id": edoc["comment_id"]},
                    {"$set": edoc},
                    upsert=True
                )
                success_count += 1
            except Exception as e:
                print(f"[ATLAS ERROR] Failed to upsert comment {edoc['comment_id']}: {e}")

        print(f"[ATLAS CLOUD SUCCESS] Successfully stored {success_count}/{len(enriched_documents)} enriched documents in MongoDB Atlas Cloud!")
    else:
        print("[ATLAS CLOUD NOTICE] Atlas connection string is unconfigured in .env; documents processed in local session.")

    print("\n" + "=" * 85)
    print("[SUCCESS] MASTER END-TO-END PIPELINE RUN COMPLETE!")
    print("=" * 85)


if __name__ == "__main__":
    run_full_end_to_end_pipeline(batch_limit=100)
