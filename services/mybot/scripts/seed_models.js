// seed_models.js - simple script to upsert model definitions into MongoDB
const { MongoClient } = require('mongodb');
require('dotenv').config({ path: require('path').resolve(__dirname, '..', '.env') });
const uri = process.env.MONGO_URI;
const DB_NAME = process.env.MONGO_DB_NAME || 'MyBot';
if (!uri) {
  console.error('MONGO_URI not set in .env; cannot seed');
  process.exit(1);
}
(async () => {
  const client = new MongoClient(uri);
  try {
    await client.connect();
    const db = client.db(DB_NAME);
    const models = db.collection('models');
    const defs = [
      { name: 'gemini', file: 'geminiService.js', active: true, description: 'Gemini model' },
      { name: 'openai', file: 'openaiService.js', active: true, description: 'OpenAI' },
      { name: 'groq', file: 'groqService.js', active: false, description: 'Groq (reviewer)' }
    ];
    for (const d of defs) {
      await models.updateOne({ name: d.name }, { $set: Object.assign({}, d, { updatedAt: new Date() }) }, { upsert: true });
      console.log('Upserted', d.name);
    }
    console.log('Done');
  } catch (e) { console.error(e); }
  process.exit(0);
})();
