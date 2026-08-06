const connectDB = require('./db');

async function test() {
  const db = await connectDB();
  const movies = await db.collection('movies').find().limit(3).toArray();
  console.log(movies);
  process.exit();
}

test();