require('dotenv').config();
const { MongoClient } = require('mongodb');

const client = new MongoClient(process.env.MONGO_URI);

async function connectDB() {
  try {
    await client.connect();
    console.log(`✅ Connected to ${process.env.MONGO_DB_NAME}`);
    return client.db(process.env.MONGO_DB_NAME);
  } catch (err) {
    console.error("❌ Connection failed:", err);
  }
}

module.exports = connectDB;