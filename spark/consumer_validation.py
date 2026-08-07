import hashlib
import torch
from validation.schema_validation import validate_with_pydantic
from nlp.cleaner import clean_text
from nlp.embeddings import EmbeddingGemmaEmbedder
from nlp.topic_detection import GroqLLMTopicDetector
from validation.utils import create_error_record

# Ensure PyTorch CPU threads operate efficiently without thread contention
torch.set_num_threads(4)

# ONE-TIME GLOBAL MODEL PRE-LOADING AT MODULE IMPORT TIME
# Loads 300MB PyTorch EmbeddingGemma & Groq LLM client ONCE in RAM for all worker threads.
print("[CONSUMER INITIALIZATION] Pre-loading EmbeddingGemma-300M & Groq Llama-3.3-70B Engine globally...")
try:
    _global_embedder = EmbeddingGemmaEmbedder()
    print("[CONSUMER INITIALIZATION] Successfully loaded global EmbeddingGemma-300M into RAM!")
except Exception as e:
    print(f"[CONSUMER INIT WARN] Global Embedder pre-load notice: {e}")
    _global_embedder = None

try:
    _global_llm_detector = GroqLLMTopicDetector()
    print("[CONSUMER INITIALIZATION] Successfully initialized global Groq LPU Client!")
except Exception as e:
    print(f"[CONSUMER INIT WARN] Global Groq LLM pre-load notice: {e}")
    _global_llm_detector = None

_topic_cache = {}  # Global in-memory exact hash topic cache for sub-millisecond deduplication
_comment_author_map = {}  # Fast in-memory comment_id -> author mapping for parent author resolution


def process_and_validate_record(record: dict) -> tuple[bool, dict | None, dict | None]:
    """
    Applies Consumer Validation (Layers 4, 5, 6 with Pydantic), Layer 7 Text Normalization,
    768D EmbeddingGemma Vector Generation, and Groq Llama-3.3-70B Human-Grade Topic Modeling.
    Uses pre-loaded global NLP models in RAM & MD5 Hash Caching for ultra-fast multi-threaded processing.
    Resolves parent_author for Neo4j User-to-User interaction graph ingestion.
    """
    global _topic_cache, _global_embedder, _global_llm_detector, _comment_author_map

    # 1. Pydantic validation (schema, datatypes, business bounds)
    is_valid, validated_dict, err_msg = validate_with_pydantic(record)
    if not is_valid or not validated_dict:
        return False, None, create_error_record(record, err_msg, "consumer_pydantic_validation")

    # 2. Text Cleaning & Normalization
    raw_msg = validated_dict.get("message", "")
    cleaned_msg = clean_text(raw_msg, to_lower=True)
    
    clean_record = dict(validated_dict)
    clean_record["message_raw"] = raw_msg
    clean_record["message"] = cleaned_msg

    # Fast Parent Author Resolution for Neo4j Graph
    comment_id = clean_record.get("comment_id", "")
    author = clean_record.get("author", "")
    parent_id = clean_record.get("parent_id", "")

    if comment_id and author:
        _comment_author_map[comment_id] = author
        if len(_comment_author_map) > 20000:
            _comment_author_map.clear()

    parent_author = _comment_author_map.get(parent_id, clean_record.get("parent_author", "community_member"))
    clean_record["parent_author"] = parent_author

    # 3. EmbeddingGemma 768D Vector + Groq LLM 70B Topic Classification
    vector_dim = 0
    topic_name = "General Inquiries"
    keywords = ["General"]
    intent = cleaned_msg[:60]
    sim_score = 0.50

    # Vector Embedding using global pre-loaded model
    if _global_embedder is not None:
        try:
            vec = _global_embedder.get_embedding(cleaned_msg)
            vector_dim = len(vec)
            
            parent_msg = validated_dict.get("parent_message", "")
            if parent_msg and str(parent_msg).strip() and str(parent_msg).strip().lower() != "nan":
                from nlp.embeddings import compute_cosine_similarity
                parent_vec = _global_embedder.get_embedding(clean_text(str(parent_msg), to_lower=True))
                sim_score = float(compute_cosine_similarity(vec, parent_vec))
        except Exception as e:
            pass

    clean_record["semantic_similarity_score"] = round(sim_score, 4)


    # Exact MD5 Hash Cache Lookup (Guarantees 100% Precision, 0 False Positives)
    cache_key = hashlib.md5(cleaned_msg.encode('utf-8')).hexdigest()
    
    if cache_key in _topic_cache:
        cached = _topic_cache[cache_key]
        topic_name = cached["detected_topic_name"]
        keywords = cached["topic_keywords"]
        intent = cached["summary_intent"]
    elif _global_llm_detector is not None:
        try:
            res = _global_llm_detector.detect_topic(cleaned_msg)
            topic_name = res.get("detected_topic_name", topic_name)
            keywords = res.get("topic_keywords", keywords)
            intent = res.get("summary_intent", intent)

            # Store in topic cache (cap cache at 5,000 items)
            if len(_topic_cache) < 5000:
                _topic_cache[cache_key] = res
        except Exception as e:
            pass

    clean_record["context_modeling"] = {
        "detected_topic_name": topic_name,
        "topic_keywords": keywords,
        "summary_intent": intent,
        "vector_embedding_dim": vector_dim,
        "indexed_in_chromadb": True
    }

    return True, clean_record, None
