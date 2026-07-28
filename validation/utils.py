from datetime import datetime


def create_error_record(raw_or_record: str | dict | None, reason: str, pipeline_stage: str) -> dict:
    """
    Constructs a standardized Dead Letter Queue (DLQ) validation error record.
    """
    return {
        "original_message": raw_or_record,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "pipeline_stage": pipeline_stage
    }
