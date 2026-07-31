import os
import pandas as pd
from nlp.embeddings import EmbeddingGemmaEmbedder
from nlp.vector_store import ConversationalVectorStore
from nlp.topic_detection import GroqLLMTopicDetector

DEVELOPMENT_DATASET_PATH = os.path.join("datasets", "development_dataset.csv")
GROQ_OUTPUT_CSV_PATH = os.path.join("datasets", "gemini_output_v2.csv")


def run_groq_llm_context_modeling_to_csv(batch_size: int = 100):
    """
    Executes Groq LLM (llama-3.3-70b-versatile) Context Modeling on 100 messages.
    Extracts 100% human-grade Topic Names, Keywords, and Summaries into datasets/gemini_output_v2.csv.
    """
    print("=" * 85)
    print("[GROQ LLM 70B CONTEXT MODELING] 100 MESSAGES -> gemini_output_v2.csv")
    print(f"   Input Dataset: '{DEVELOPMENT_DATASET_PATH}' | Batch: {batch_size} records")
    print(f"   Output CSV:    '{GROQ_OUTPUT_CSV_PATH}'")
    print("=" * 85)

    if not os.path.exists(DEVELOPMENT_DATASET_PATH):
        print(f"[ERROR] Required dataset '{DEVELOPMENT_DATASET_PATH}' not found!")
        return

    # 1. Read 100 raw records from development_dataset.csv
    print(f"[1/4] Reading {batch_size} raw records from '{DEVELOPMENT_DATASET_PATH}'...")
    df_raw = pd.read_csv(DEVELOPMENT_DATASET_PATH, nrows=batch_size, encoding="utf-8", on_bad_lines="skip")
    df_raw["message"] = df_raw["message"].fillna("").astype(str)
    df_raw["author"] = df_raw["author"].fillna("anonymous").astype(str)

    # Filter empty/deleted posts
    df_clean = df_raw[~df_raw["message"].isin(["[deleted]", "[removed]", ""])].copy()
    print(f"      Loaded {len(df_clean)} valid conversational messages.")

    # 2. Store EmbeddingGemma 768D Vectors in ChromaDB
    print(f"\n[2/4] Indexing {len(df_clean)} message vectors into ChromaDB Vector DB...")
    vstore = ConversationalVectorStore(collection_name="groq_context_store")
    messages_payload = [
        {
            "msg_id": str(row.get("comment_id", f"c_{i}")),
            "text": str(row["message"]),
            "author": str(row["author"])
        }
        for i, row in df_clean.iterrows()
    ]
    vstore.add_messages(messages_payload)

    # 3. Analyze each message via Groq LPU (llama-3.3-70b-versatile)
    print("\n[3/4] Running Groq LLM (llama-3.3-70b-versatile) Context Classification Engine...")
    detector = GroqLLMTopicDetector()

    detected_topics = []
    topic_keywords_list = []
    summary_intents = []

    for idx, row in df_clean.iterrows():
        msg_text = str(row["message"])
        result = detector.detect_topic(msg_text)
        
        detected_topics.append(result["detected_topic_name"])
        topic_keywords_list.append(", ".join(result["topic_keywords"]))
        summary_intents.append(result["summary_intent"])

        if (len(detected_topics)) % 10 == 0 or len(detected_topics) == len(df_clean):
            print(f"      Processed {len(detected_topics)}/{len(df_clean)} messages via Groq LLM...")

    df_clean["detected_topic_name"] = detected_topics
    df_clean["topic_keywords"] = topic_keywords_list
    df_clean["summary_intent"] = summary_intents

    # 4. Save Enriched Output to CSV (gemini_output_v2.csv)
    print(f"\n[4/4] Saving Human-Grade Enriched Predictions to '{GROQ_OUTPUT_CSV_PATH}'...")
    output_columns = [
        "comment_id", "author", "message", "detected_topic_name", "topic_keywords", "summary_intent"
    ]
    
    save_cols = [c for c in output_columns if c in df_clean.columns]
    df_output = df_clean[save_cols].copy()
    
    try:
        df_output.to_csv(GROQ_OUTPUT_CSV_PATH, index=False, encoding="utf-8")
        print(f"\n[SUCCESS] Successfully generated '{GROQ_OUTPUT_CSV_PATH}' with {len(df_output)} rows!")
    except Exception as e:
        alt_path = os.path.join("datasets", "groq_output_llm.csv")
        df_output.to_csv(alt_path, index=False, encoding="utf-8")
        print(f"\n[SUCCESS] Saved to '{alt_path}' ({e})!")

    print("=" * 85)

    # Display preview table in terminal
    print("\n[PREVIEW OF GROQ LLM OUTPUT] (Top 15 Rows)")
    print("-" * 85)
    display_df = df_output[["comment_id", "author", "message", "detected_topic_name"]].head(15).copy()
    display_df["comment_id"] = display_df["comment_id"].astype(str).str.slice(0, 10) + "..."
    display_df["author"] = display_df["author"].astype(str).str.encode("ascii", "ignore").str.decode("ascii").str.slice(0, 12)
    display_df["message"] = display_df["message"].apply(lambda x: str(x).encode("ascii", "ignore").decode("ascii")).str.slice(0, 40) + "..."

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)
    print(display_df.to_string(index=False))
    print("-" * 85)


if __name__ == "__main__":
    run_groq_llm_context_modeling_to_csv(batch_size=100)
