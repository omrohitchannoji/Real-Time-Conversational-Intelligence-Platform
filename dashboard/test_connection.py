from pymongo import MongoClient


client = MongoClient(
    "mongodb+srv://omrohitchannoji7_db_user:NP8N1SBGSW9Q2XuA@context-modeling-cluste.maly4h1.mongodb.net/"
)


print(
    client.list_database_names()
)