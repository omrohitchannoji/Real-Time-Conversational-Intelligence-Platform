from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Optional
from pyspark.sql.types import StructType, StructField, StringType

REQUIRED_FIELDS = ["comment_id", "author", "message", "created_utc"]


class MessageModel(BaseModel):
    """
    Pydantic Validation Model for Conversational Messages.
    Enforces Layer 1 Input Validation, Datatypes, and Business Rules.
    """
    comment_id: str = Field(..., min_length=1, description="Unique comment identifier")
    parent_id: Optional[str] = Field(default=None, description="Parent comment ID for reply threads")
    author: str = Field(..., min_length=1, description="User/Author username")
    created_utc: str = Field(..., min_length=1, description="ISO/UTC Creation timestamp")
    message: str = Field(..., min_length=1, max_length=5000, description="Message text body")
    source: Optional[str] = Field(default="reddit", description="Platform source name")

    @field_validator("author")
    def validate_author_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Author name cannot be empty or whitespace")
        return v.strip()

    @field_validator("message")
    def validate_message_body(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message body cannot be empty or whitespace")
        if len(v) > 5000:
            return v[:4995] + "..."
        return v


def validate_with_pydantic(record: dict) -> tuple[bool, dict | None, str]:
    """
    Validates a dictionary record using Pydantic MessageModel.
    Returns (is_valid, validated_dict, error_message)
    """
    if not isinstance(record, dict):
        return False, None, "Record is not a JSON object/dict"

    try:
        validated = MessageModel.model_validate(record)
        return True, validated.model_dump(), ""
    except ValidationError as e:
        # Extract first readable error description from Pydantic
        errors = e.errors()
        err_msg = f"{errors[0]['loc'][0]}: {errors[0]['msg']}" if errors else str(e)
        return False, None, f"Pydantic Validation Failure: {err_msg}"


# PySpark StructType Schema for Kafka JSON Stream Parsing
SPARK_MESSAGE_SCHEMA = StructType([
    StructField("comment_id", StringType(), True),
    StructField("parent_id", StringType(), True),
    StructField("author", StringType(), True),
    StructField("created_utc", StringType(), True),
    StructField("message", StringType(), True),
    StructField("source", StringType(), True)
])
