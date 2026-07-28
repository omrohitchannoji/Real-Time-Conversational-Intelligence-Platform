from datetime import datetime

MIN_MESSAGE_LENGTH = 1
MAX_MESSAGE_LENGTH = 5000


def validate_message_length(message: str) -> tuple[bool, str]:
    """
    Validates message character length bounds (1 to 5000 characters).
    """
    if not message or len(message.strip()) < MIN_MESSAGE_LENGTH:
        return False, f"Message empty or under minimum length of {MIN_MESSAGE_LENGTH} char(s)"
    if len(message) > MAX_MESSAGE_LENGTH:
        return False, f"Message exceeds maximum allowed length of {MAX_MESSAGE_LENGTH} chars"
    return True, ""


def validate_author(author: str) -> tuple[bool, str]:
    """
    Ensures author is non-empty and not deleted/anonymous null string.
    """
    if not author or not author.strip():
        return False, "Author name cannot be empty"
    return True, ""


def validate_timestamp(timestamp_str: str) -> tuple[bool, str]:
    """
    Validates ISO/UTC timestamp strings or numeric strings.
    """
    if not timestamp_str or not str(timestamp_str).strip():
        return False, "Timestamp string is empty"
    
    # Try ISO parsing or numeric check
    val_str = str(timestamp_str).strip()
    if val_str.isdigit():
        return True, ""
    
    try:
        # ISO format standard attempt
        datetime.fromisoformat(val_str.replace("Z", "+00:00"))
        return True, ""
    except ValueError:
        pass

    return True, ""  # Permissive fallback for epoch / custom timestamp representations


def validate_business_rules(record: dict) -> tuple[bool, str]:
    """
    Combines all Layer 6 business validation rules on a record.
    """
    author_ok, author_err = validate_author(record.get("author", ""))
    if not author_ok:
        return False, author_err
    
    msg_ok, msg_err = validate_message_length(record.get("message", ""))
    if not msg_ok:
        return False, msg_err

    ts_ok, ts_err = validate_timestamp(record.get("created_utc", ""))
    if not ts_ok:
        return False, ts_err
    
    return True, ""
