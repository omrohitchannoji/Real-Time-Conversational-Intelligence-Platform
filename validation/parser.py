import json


def decode_utf8_bytes(raw_bytes: bytes) -> tuple[bool, str, str]:
    """
    Decodes raw bytes into a UTF-8 string.
    Returns (success, decoded_string, error_message)
    """
    try:
        decoded = raw_bytes.decode("utf-8")
        return True, decoded, ""
    except Exception as e:
        return False, "", f"UTF-8 Decoding failure: {str(e)}"


def parse_json_message(json_str: str) -> tuple[bool, dict | None, str]:
    """
    Parses JSON string into a Python dictionary.
    Returns (success, parsed_dict, error_message)
    """
    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            return False, None, "Parsed JSON is not a JSON dictionary object"
        return True, data, ""
    except Exception as e:
        return False, None, f"JSON parsing failure: {str(e)}"
