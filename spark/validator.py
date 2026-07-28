from pyspark.sql.functions import col

def validate_messages(df):
    return df.filter(
        col("comment_id").isNotNull() &
        col("author").isNotNull() &
        col("message").isNotNull()
    )