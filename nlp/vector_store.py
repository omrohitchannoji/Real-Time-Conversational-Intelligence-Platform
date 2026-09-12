import sys
if sys.platform.startswith("linux"):
    try:
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass

import chromadb
import numpy as np
from nlp.embeddings import EmbeddingGemmaEmbedder


class ConversationalVectorStore:
    """
    Industry-Standard ChromaDB Vector Database Manager.
    Stores dense 768-dim EmbeddingGemma vectors, text messages, and metadata for ultra-fast
    Approximate Nearest Neighbor (ANN) vector similarity search & topic clustering.
    """
    def __init__(self, collection_name: str = "conversational_context_store"):
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db_store")
        self.embedder = EmbeddingGemmaEmbedder()
        self.collection_name = collection_name

        # Reset or create collection
        try:
            self.chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass

        self.collection = self.chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"[VECTOR DB] Initialized ChromaDB In-Memory Collection '{collection_name}'.")

    def add_messages(self, messages: list[dict]):
        """
        Takes a list of message dicts ({'msg_id': 'c_1', 'text': '...', 'author': '...'}),
        generates 768-dim EmbeddingGemma vectors, and stores them in ChromaDB Vector Database.
        """
        if not messages:
            return

        ids = [m["msg_id"] for m in messages]
        texts = [m["text"] for m in messages]
        metadatas = [{"author": m.get("author", "user"), "timestamp": m.get("timestamp", "")} for m in messages]

        # Generate EmbeddingGemma vectors
        embeddings = self.embedder.get_batch_embeddings(texts).tolist()

        # Store in ChromaDB Vector DB
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        print(f"[VECTOR DB] Indexed {len(messages)} message vectors into ChromaDB!")

    def query_similar(self, query_text: str, top_k: int = 3) -> list[dict]:
        """
        Performs ultra-fast ANN vector similarity search against ChromaDB for a query message.
        """
        query_vec = self.embedder.get_embedding(query_text)
        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        matches = []
        if results and results.get("ids"):
            matched_ids = results["ids"][0]
            matched_docs = results["documents"][0]
            matched_metas = results["metadatas"][0]
            matched_dists = results["distances"][0]

            for mid, doc, meta, dist in zip(matched_ids, matched_docs, matched_metas, matched_dists):
                similarity = round(float(1.0 - dist), 4)
                matches.append({
                    "msg_id": mid,
                    "text": doc,
                    "author": meta.get("author"),
                    "cosine_similarity": max(0.0, similarity)
                })

        return matches


if __name__ == "__main__":
    vstore = ConversationalVectorStore()
    sample_msgs = [
        {"msg_id": "c_1", "text": "NVIDIA just announced their new Blackwell GPU architecture for LLM training clusters.", "author": "tech_guru"},
        {"msg_id": "c_2", "text": "The 8TB/s memory bandwidth is insane compared to the H100!", "author": "hardware_dev"},
        {"msg_id": "c_3", "text": "CRISPR gene editing therapy has received landmark FDA approval.", "author": "gene_doc"},
        {"msg_id": "c_4", "text": "Grand Theft Auto VI trailer hit 200 million views on YouTube!", "author": "gamer_alex"}
    ]

    vstore.add_messages(sample_msgs)

    search_query = "What are the latest developments in AI graphics chips?"
    print(f"\n[VECTOR DB QUERY] Query: '{search_query}'")
    matches = vstore.query_similar(search_query, top_k=2)
    for m in matches:
        print(f"  * Match [ID: {m['msg_id']}] (Sim: {m['cosine_similarity']:.4f}) | Author: {m['author']} | Text: '{m['text']}'")
