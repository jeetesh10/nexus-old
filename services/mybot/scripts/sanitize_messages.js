#!/usr/bin/env node
// sanitize_messages.js
// One-off script: connect to Mongo, find assistant messages containing critique/review text,
// sanitize the text by stripping critique sections and saving the cleaned reply back.

const { MongoClient } = require('mongodb');

function getDbNameFromUri(uri) {
  if (!uri) return null;
  try {
    const m = uri.match(/\/([^\/\?]+)(?:\?|$)/);
    if (m && m[1]) return m[1];
  } catch (e) {}
  return null;
}

const { sanitizeFinalText, extractSuggestedReply } = require('../src/services/orchestrationUtils');

async function main() {
  const MONGO_URI = process.env.MONGO_URI;
  if (!MONGO_URI) {
    console.error('MONGO_URI not set in environment. Aborting.');
    process.exit(1);
  }
  const DB_NAME = process.env.MONGO_DB_NAME || getDbNameFromUri(MONGO_URI) || 'MyBot';

  const client = new MongoClient(MONGO_URI);
  await client.connect();
  const db = client.db(DB_NAME);
  const col = db.collection('messages');

  // Find assistant messages that appear to contain critique or suggested reply sections
  const cursor = col.find({ role: 'assistant', text: { $regex: '(Critique|Suggested|Suggested Improved Reply|Suggested improved reply)', $options: 'i' } });
  let count = 0;
  while (await cursor.hasNext()) {
    const doc = await cursor.next();
    const oldText = doc.text || '';
    const cleaned = sanitizeFinalText(oldText);
    if (!cleaned || cleaned.length === 0) continue;
    if (cleaned === oldText) continue; // nothing changed
    await col.updateOne({ _id: doc._id }, { $set: { text: cleaned, sanitizedAt: new Date(), sanitizer: 'sanitize_messages.js' } });
    count++;
    console.log('Updated', String(doc._id), '->', cleaned.slice(0, 120).replace(/\n/g, ' '));
  }
  console.log('Sanitization complete. Documents updated:', count);
  await client.close();
}

main().catch(e => { console.error(e); process.exit(1); });
