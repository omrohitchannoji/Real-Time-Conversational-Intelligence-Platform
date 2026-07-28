from database.mongo_connection import validation_errors_col


def log_validation_errors(error_records: list[dict]):
    """
    Writes invalid / rejected records to the Dead Letter Queue ('validation_errors' collection).
    """
    if error_records:
        validation_errors_col.insert_many(error_records, ordered=False)
