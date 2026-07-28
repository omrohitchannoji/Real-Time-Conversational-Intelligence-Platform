from validation.schema_validation import validate_with_pydantic
from nlp.cleaner import clean_text
from validation.utils import create_error_record


def process_and_validate_record(record: dict) -> tuple[bool, dict | None, dict | None]:
    """
    Applies Consumer Validation (Layers 4, 5, 6 with Pydantic) & Layer 7 Text Normalization.
    Returns (is_valid, cleaned_valid_record, dlq_error_record)
    """
    # 1. Pydantic validation (schema, datatypes, business bounds)
    is_valid, validated_dict, err_msg = validate_with_pydantic(record)
    if not is_valid or not validated_dict:
        return False, None, create_error_record(record, err_msg, "consumer_pydantic_validation")

    # 2. Layer 7 Text Cleaning & Normalization
    raw_msg = validated_dict.get("message", "")
    cleaned_msg = clean_text(raw_msg, to_lower=True)
    
    clean_record = dict(validated_dict)
    clean_record["message_raw"] = raw_msg
    clean_record["message"] = cleaned_msg

    return True, clean_record, None
