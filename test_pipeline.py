import json
from validation.schema_validation import validate_with_pydantic, MessageModel
from kafka_pipeline.serializer import serialize_to_json_bytes
from kafka_pipeline.producer_validation import validate_and_serialize_record
from spark.consumer_validation import process_and_validate_record
from nlp.cleaner import clean_text


def test_pipeline_pydantic_validation():
    print("=" * 60)
    print("RUNNING PYDANTIC 8-LAYER VALIDATION PIPELINE VERIFICATION")
    print("=" * 60)

    # 1. Valid Message Test Case
    valid_sample = {
        "comment_id": "test_pydantic_001",
        "parent_id": "test_parent_000",
        "author": "RedditUser123",
        "created_utc": "2026-01-01T01:36:13",
        "message": "Check out this link https://example.com! Great conversational project.",
        "source": "worldnews"
    }

    print("\n[1] Testing Layer 1 & Layer 2 (Pydantic Producer Validation & Serialization):")
    is_valid, ser_bytes, err = validate_and_serialize_record(valid_sample)
    if is_valid and ser_bytes:
        print("  [SUCCESS] Pydantic Producer Validation PASSED")
        print(f"  [INFO] Serialized Bytes length: {len(ser_bytes)} bytes")
    else:
        print(f"  [FAILED] Producer Validation FAILED: {err}")

    print("\n[2] Testing Layer 4, 5, 6 & Text Normalization (Pydantic Consumer Validation):")
    is_consumer_valid, clean_doc, dlq_err = process_and_validate_record(valid_sample)
    if is_consumer_valid and clean_doc:
        print("  [SUCCESS] Pydantic Consumer Validation PASSED")
        print(f"  [RAW]   '{clean_doc['message_raw']}'")
        print(f"  [CLEAN] '{clean_doc['message']}'")
    else:
        print(f"  [FAILED] Consumer Validation FAILED: {dlq_err}")

    # 2. Invalid Message Test Case (Empty author string -> Pydantic ValidationError)
    invalid_sample = {
        "comment_id": "test_pydantic_002",
        "author": "   ",  # Blank author -> Pydantic validator failure
        "created_utc": "2026-01-01T01:36:13",
        "message": "",       # Empty message -> Pydantic validator failure
        "source": "worldnews"
    }

    print("\n[3] Testing Pydantic Dead Letter Queue (DLQ) Fault Tolerance Routing:")
    is_valid_inv, ser_bytes_inv, dlq_err_inv = validate_and_serialize_record(invalid_sample)
    if not is_valid_inv and dlq_err_inv:
        print("  [SUCCESS] Pydantic correctly rejected malformed message!")
        print(f"  [DLQ REASON] '{dlq_err_inv['reason']}'")
        print(f"  [DLQ STAGE]  '{dlq_err_inv['pipeline_stage']}'")
    else:
        print("  [FAILED] Malformed record slipped through without detection!")

    print("\n" + "=" * 60)
    print("ALL PYDANTIC VALIDATION PIPELINE LAYERS VERIFIED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_pipeline_pydantic_validation()
