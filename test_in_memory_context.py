import os
import pandas as pd
from nlp.embeddings import GeminiEmbedder
from nlp.vector_store import ConversationalVectorStore
from nlp.topic_detection import UnsupervisedTopicDetector

# Clean Sample Conversational Messages for Live In-Memory Prediction Testing
SAMPLE_CONVERSATIONS = [
    {"msg_id": "m_101", "text": "NVIDIA just announced their new Blackwell GPU architecture for LLM training clusters.", "author": "tech_guru_99"},
    {"msg_id": "m_102", "text": "The 8TB/s memory bandwidth is insane compared to the H100!", "author": "hardware_dev"},
    {"msg_id": "m_103", "text": "Does AWS or Azure have preview GPU instances available yet?", "author": "cloud_architect"},
    {"msg_id": "m_104", "text": "CRISPR gene editing therapy has received landmark FDA approval for sickle cell disease.", "author": "gene_scientist"},
    {"msg_id": "m_105", "text": "Bone marrow stem cells are extracted, edited in the lab, and re-infused.", "author": "bio_student"},
    {"msg_id": "m_106", "text": "The UEFA Champions League final delivered an absolute tactical masterclass!", "author": "football_fanatic"},
    {"msg_id": "m_107", "text": "The high-pressing defense completely suffocated their counter-attacks in the second half.", "author": "tactics_guru"},
    {"msg_id": "m_108", "text": "Grand Theft Auto VI trailer hit 200 million views on YouTube!", "author": "gamer_alex"},
    {"msg_id": "m_109", "text": "The NPC density in Vice City looks next-level compared to GTA V.", "author": "console_gamer"},
    {"msg_id": "m_110", "text": "NASA Artemis III mission targets human landing near the lunar South Pole.", "author": "lunar_observer"}
]


def run_in_memory_context_test():
    """
    Live In-Memory Context Modeling & Vector Database Terminal Test.
    Zero CSV writing. Demonstrates real-time Gemini Embeddings, ChromaDB Vector DB,
    and Unsupervised TopicBERT predictions.
    """
    print("=" * 80)
    print("[TEST] IN-MEMORY CONVERSATIONAL CONTEXT MODELING & VECTOR DB")
    print("=" * 80)

    # 1. Initialize ChromaDB Vector Database & Index Sample Messages
    vstore = ConversationalVectorStore(collection_name="test_context_store")
    vstore.add_messages(SAMPLE_CONVERSATIONS)

    # 2. Autonomous TopicBERT Clustering on Embeddings
    print("\n[TOPIC DISCOVERY] Running Unsupervised TopicBERT Clustering...")
    texts = [m["text"] for m in SAMPLE_CONVERSATIONS]
    detector = UnsupervisedTopicDetector(num_topics=4)
    topic_ids, topic_summary = detector.fit_predict(texts)

    # 3. Print Discovered Dynamic Topic Clusters
    print("\n" + "=" * 80)
    print("[DISCOVERED TOPIC CLUSTERS]")
    print("=" * 80)
    for tid, info in topic_summary.items():
        print(f"  * {info['name']}")
        print(f"    - Messages Count: {info['message_count']}")
        print(f"    - Key Terms: {', '.join(info['top_keywords'])}\n")

    # 4. Print In-Memory Prediction Results Table
    print("=" * 80)
    print("[PREDICTION TABLE] IN-MEMORY CONTEXT CLUSTERING RESULTS")
    print("=" * 80)

    results_data = []
    for msg_obj, tid in zip(SAMPLE_CONVERSATIONS, topic_ids):
        results_data.append({
            "Msg ID": msg_obj["msg_id"],
            "Author": msg_obj["author"],
            "Message Text": msg_obj["text"][:45] + "...",
            "Discovered Topic": topic_summary[tid]["name"]
        })

    df_results = pd.DataFrame(results_data)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)
    print(df_results.to_string(index=False))

    # 5. Live Vector Database Similarity Query Test
    print("\n" + "=" * 80)
    print("[LIVE VECTOR DB QUERY TEST]")
    print("=" * 80)
    query_text = "What is the latest news on AI graphics hardware and GPU servers?"
    print(f"Query Text: '{query_text}'\n")

    matches = vstore.query_similar(query_text, top_k=3)
    print("Top Vector Similarity Matches in ChromaDB:")
    for rank, m in enumerate(matches, 1):
        print(f"  #{rank} [Similarity: {m['cosine_similarity']:.4f}] | Author: {m['author']}")
        print(f"      Text: '{m['text']}'\n")

    print("=" * 80)


if __name__ == "__main__":
    run_in_memory_context_test()
