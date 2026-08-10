import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import pandas as pd
from nlp.embeddings import EmbeddingGemmaEmbedder, compute_cosine_similarity


class RelationshipInferencer:
    """
    Relationship Inference Engine.
    Infers semantic, structural, and social relationships between messages and authors
    using parent-child vector cosine similarity (EmbeddingGemma) and structural message pairs.
    """
    def __init__(self):
        self.embedder = EmbeddingGemmaEmbedder()

    def infer_message_relationships(self, df_records: pd.DataFrame) -> pd.DataFrame:
        """
        Processes message records from development_dataset.csv, calculates vector embeddings,
        computes parent-child Cosine Similarity scores, and assigns relationship classifications.
        """
        print(f"[RELATIONSHIP ENGINE] Processing {len(df_records)} records for Relationship Inference...")
        results = []

        for idx, row in df_records.iterrows():
            msg_id = str(row.get("comment_id", ""))
            parent_id = str(row.get("parent_id", ""))
            author = str(row.get("author", ""))
            parent_author = str(row.get("parent_author", ""))
            msg_text = str(row.get("message", ""))
            parent_text = str(row.get("parent_message", ""))

            # Calculate vector embeddings
            msg_vec = self.embedder.get_embedding(msg_text)
            
            sim_score = 0.0
            rel_type = "ROOT_POST" if not parent_id or parent_id == "t3_none" or parent_id == "nan" else "DIRECT_REPLY"

            if parent_text and parent_text != "nan" and len(parent_text.strip()) > 3:
                parent_vec = self.embedder.get_embedding(parent_text)
                sim_score = compute_cosine_similarity(msg_vec, parent_vec)
                
                # Classify relationship semantics
                if sim_score >= 0.70:
                    rel_classification = "TOPIC_CONTINUATION"
                elif sim_score >= 0.45:
                    rel_classification = "TOPIC_ELABORATION"
                else:
                    rel_classification = "TOPIC_SHIFT"
            else:
                rel_classification = "INDEPENDENT_THREAD" if rel_type == "ROOT_POST" else "UNLINKED_REPLY"

            results.append({
                "comment_id": msg_id,
                "parent_id": parent_id,
                "author": author,
                "parent_author": parent_author if parent_author and parent_author != "nan" else "system",
                "semantic_similarity_score": round(float(sim_score), 4),
                "relationship_type": rel_type,
                "relationship_classification": rel_classification
            })

        return pd.DataFrame(results)

    def calculate_author_social_graph(self, df_relationships: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates author-to-author social relationship weights based on reply frequencies
        and average semantic similarity alignment.
        """
        # Filter valid user interactions
        valid_pairs = df_relationships[
            (df_relationships["parent_author"] != "system") &
            (df_relationships["parent_author"] != "nan") &
            (df_relationships["author"] != df_relationships["parent_author"])
        ]

        if valid_pairs.empty:
            return pd.DataFrame(columns=["source_author", "target_author", "reply_count", "avg_semantic_similarity", "interaction_weight"])

        grouped = valid_pairs.groupby(["author", "parent_author"]).agg(
            reply_count=("comment_id", "count"),
            avg_semantic_similarity=("semantic_similarity_score", "mean")
        ).reset_index()

        grouped.rename(columns={"author": "source_author", "parent_author": "target_author"}, inplace=True)
        grouped["avg_semantic_similarity"] = grouped["avg_semantic_similarity"].round(4)
        grouped["interaction_weight"] = (grouped["reply_count"] * (1.0 + grouped["avg_semantic_similarity"])).round(4)

        return grouped.sort_values(by="interaction_weight", ascending=False)


class RelationshipInferenceEngine:
    """
    Graph-based Relationship Inference Engine wrapping UserInteractionGraphBuilder.
    """
    def __init__(self, builder=None):
        self.builder = builder
        self.inferencer = RelationshipInferencer()

    def detect_co_participation(self) -> list[dict]:
        """Detects co-participation threads in user interaction graph."""
        if not self.builder or not self.builder.graph:
            return []
        co_parts = []
        for u, v in self.builder.graph.edges():
            co_parts.append({"user_a": u, "user_b": v, "co_participation_count": self.builder.graph[u][v].get("weight", 1)})
        return co_parts

    def find_reciprocal_pairs(self) -> list[tuple]:
        """Detects reciprocal communication pairs in graph."""
        if not self.builder or not self.builder.graph:
            return []
        recip = []
        for u, v in self.builder.graph.edges():
            if self.builder.graph.has_edge(v, u) and u < v:
                recip.append((u, v))
        return recip


if __name__ == "__main__":
    test_data = pd.DataFrame([
        {
            "comment_id": "c_1001",
            "parent_id": "t3_none",
            "author": "tech_guru",
            "parent_author": "system",
            "message": "NVIDIA just announced their new Blackwell GPU architecture for LLM training clusters.",
            "parent_message": ""
        },
        {
            "comment_id": "c_1002",
            "parent_id": "c_1001",
            "author": "hardware_dev",
            "parent_author": "tech_guru",
            "message": "The 8TB/s memory bandwidth is insane compared to the H100!",
            "parent_message": "NVIDIA just announced their new Blackwell GPU architecture for LLM training clusters."
        },
        {
            "comment_id": "c_1003",
            "parent_id": "c_1002",
            "author": "cloud_architect",
            "parent_author": "hardware_dev",
            "message": "True, but the power consumption per node is going to be massive at 1200W.",
            "parent_message": "The 8TB/s memory bandwidth is insane compared to the H100!"
        },
        {
            "comment_id": "c_1004",
            "parent_id": "c_1001",
            "author": "sports_fan",
            "parent_author": "tech_guru",
            "message": "Did anyone watch the UEFA Champions League final yesterday?",
            "parent_message": "NVIDIA just announced their new Blackwell GPU architecture for LLM training clusters."
        }
    ])

    inferencer = RelationshipInferencer()
    df_rel = inferencer.infer_message_relationships(test_data)
    df_social = inferencer.calculate_author_social_graph(df_rel)

    print("=" * 65)
    print("[TEST] Relationship Inference Engine Output")
    print("=" * 60)
    print(df_rel[["comment_id", "author", "parent_author", "semantic_similarity_score", "relationship_classification"]])
    print("\n[TEST] Author Social Graph Interaction Matrix:")
    print(df_social)
