import json
from validation.parser import decode_utf8_bytes


def serialize_to_json_bytes(record: dict) -> tuple[bool, bytes | None, str]:
    """
    Layer 2 Serialization Validation:
    Converts a Python dictionary to UTF-8 encoded JSON bytes.
    Returns (success, json_bytes, error_message)
    """
    try:
        json_str = json.dumps(record, ensure_ascii=False)
        json_bytes = json_str.encode("utf-8")
        
        # Verify decoding validity
        ok, _, err = decode_utf8_bytes(json_bytes)
        if not ok:
            return False, None, err
            
        return True, json_bytes, ""
    except Exception as e:
        return False, None, f"Serialization Error: {str(e)}"
