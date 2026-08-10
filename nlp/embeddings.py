import os
import numpy as np
from dotenv import load_dotenv

load_dotenv(override=True)

MODEL_NAME = "google/embeddinggemma-300m"
_st_model = None


def _deterministic_fallback_vector(text: str, dim: int = 768) -> np.ndarray:
    """Fallback deterministic vector generator when SentenceTransformer is unavailable."""
    import hashlib
    if not text or not text.strip():
        return np.zeros(dim, dtype=np.float32)
    words = text.lower().split()
    vec = np.zeros(dim, dtype=np.float32)
    for word in words:
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        val = ((h >> 16) % 1000) / 1000.0 - 0.5
        vec[idx] += val
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


def get_embeddinggemma_model():
    """
    Loads Google EmbeddingGemma-300M model from HuggingFace via SentenceTransformer.
    Uses HF_TOKEN automatically from environment. Fallback if unavailable.
    """
    global _st_model
    if _st_model is not None:
        return _st_model

    try:
        from sentence_transformers import SentenceTransformer
        hf_token = os.getenv("HF_TOKEN", os.getenv("HUGGINGFACE_TOKEN", ""))
        print(f"[EMBEDDING ENGINE] Loading HuggingFace Model '{MODEL_NAME}'...")
        kwargs = {"trust_remote_code": True}
        if hf_token:
            kwargs["token"] = hf_token

        _st_model = SentenceTransformer(MODEL_NAME, **kwargs)
        print(f"[EMBEDDING ENGINE] Successfully loaded '{MODEL_NAME}'!")
        return _st_model
    except Exception as e:
        print(f"[EMBEDDING ENGINE WARN] Could not load '{MODEL_NAME}': {e}. Using deterministic fallback embedder.")
        _st_model = "FALLBACK"
        return _st_model


class EmbeddingGemmaEmbedder:
    """
    Google EmbeddingGemma-300M Vector Generator (via HuggingFace SentenceTransformer or deterministic fallback).
    Zero Gemini API calls, zero quota limits! Runs locally.
    """
    def __init__(self):
        self.model = get_embeddinggemma_model()

    def get_embedding(self, text: str) -> list[float]:
        """
        Generates dense semantic vector for a single text using google/embeddinggemma-300m or fallback.
        """
        if not text or not text.strip():
            return [0.0] * 768

        if self.model == "FALLBACK":
            return _deterministic_fallback_vector(text, 768).tolist()

        try:
            vec = self.model.encode(text, convert_to_numpy=True)
            return vec.tolist()
        except Exception as e:
            print(f"[EMBEDDING ERROR] Encoding failure: {e}. Using fallback.")
            return _deterministic_fallback_vector(text, 768).tolist()

    def get_batch_embeddings(self, texts: list[str]) -> np.ndarray:
        """
        Generates dense vectors for a list of message texts via google/embeddinggemma-300m or fallback.
        """
        print(f"[EMBEDDING ENGINE] Encoding batch of {len(texts)} messages...")
        if self.model == "FALLBACK":
            return np.array([_deterministic_fallback_vector(t, 768) for t in texts], dtype=np.float32)

        try:
            vecs = self.model.encode(texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True)
            return vecs
        except Exception as e:
            print(f"[EMBEDDING ERROR] Batch encoding failure: {e}. Using fallback.")
            return np.array([_deterministic_fallback_vector(t, 768) for t in texts], dtype=np.float32)





def compute_cosine_similarity(vec1: list[float] | np.ndarray, vec2: list[float] | np.ndarray) -> float:
    """
    Computes Cosine Similarity between two EmbeddingGemma vectors.
    """
    v1 = np.array(vec1, dtype=np.float32)
    v2 = np.array(vec2, dtype=np.float32)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    sim = np.dot(v1, v2) / (norm1 * norm2)
    return float(np.clip(sim, 0.0, 1.0))


if __name__ == "__main__":
    embedder = EmbeddingGemmaEmbedder()
    sample_text = "NVIDIA's new Blackwell GPU architecture revolutionizes LLM training clusters."
    vec = embedder.get_embedding(sample_text)
    print("=" * 65)
    print(f"[TEST] HuggingFace '{MODEL_NAME}' Vector Generator")
    print("=" * 65)
    print(f"Sample Input: '{sample_text}'")
    print(f"Vector Dimensions: {len(vec)}")
    print(f"First 5 Vector Values: {vec[:5]}")
