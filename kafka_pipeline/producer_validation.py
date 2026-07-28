from validation.schema_validation import validate_with_pydantic, MessageModel
from kafka_pipeline.serializer import serialize_to_json_bytes
from validation.utils import create_error_record


def validate_and_serialize_record(record: dict) -> tuple[bool, bytes | None, dict | None]:
    """
    Applies Layer 1 & Layer 2 Validation on candidate records using Pydantic.
    Returns (is_valid, serialized_bytes, dlq_error_record)
    """
    # 1. Layer 1 Pydantic Validation (Required fields, datatypes, business rules)
    is_valid, validated_dict, err_msg = validate_with_pydantic(record)
    if not is_valid or not validated_dict:
        dlq_obj = create_error_record(record, err_msg, "layer1_pydantic_validation")
        return False, None, dlq_obj

    # 2. Layer 2 Serialization Validation
    ser_ok, ser_bytes, ser_err = serialize_to_json_bytes(validated_dict)
    if not ser_ok:
        dlq_obj = create_error_record(record, ser_err, "layer2_serialization")
        return False, None, dlq_obj

    return True, ser_bytes, None
