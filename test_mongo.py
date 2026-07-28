from database.mongo_connection import messages

sample = {
    "comment_id": "test001",
    "author": "om",
    "message": "MongoDB connection successful!"
}

result = messages.insert_one(sample)

print("Inserted ID:", result.inserted_id)