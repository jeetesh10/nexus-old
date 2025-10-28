// mongoService.js
// Lightweight MongoDB helper used by the chat API.

const { MongoClient } = require('mongodb');

let client = null;
let db = null;
let warnedNoUri = false;

const debug = process.env.DEBUG === 'true';

async function connect() {
  if (debug) console.log('[mongoService] Entering connect');
  const MONGO_URI = process.env.MONGO_URI;
  let DB_NAME = process.env.MONGO_DB_NAME ? process.env.MONGO_DB_NAME.trim() : '';
  if (!DB_NAME && MONGO_URI) {
    try {
      const m = MONGO_URI.match(/\/(?:[^\/\?]+)\/?(?:\?|$)/);
      if (m && m[0]) {
        DB_NAME = m[0].replace(/^\//, '').replace(/\?.*$/, '');
      }
    } catch (e) {
      // ignore
    }
  }
  if (!DB_NAME) DB_NAME = 'MyBot';
  if (!MONGO_URI) {
    if (!warnedNoUri) {
      console.warn('[mongoService] MONGO_URI not set; mongoService will be a no-op.');
      warnedNoUri = true;
    }
    return null;
  }
  if (db) {
    if (debug) console.log('[mongoService] Already connected, returning db');
    return db;
  }
  client = new MongoClient(MONGO_URI);
  if (debug) console.log('[mongoService] Connecting to Mongo', { uri: MONGO_URI, dbName: DB_NAME });
  await client.connect();
  db = client.db(DB_NAME);
  console.log('[mongoService] mongoService connected to', DB_NAME);
  
  // Ensure indexes for performance
  if (debug) console.log('[mongoService] Ensuring indexes');
  await ensureIndexes();
  
  return db;
}

async function ensureIndexes() {
  try {
    if (debug) console.log('[mongoService] Creating indexes for projects');
    const projectsCol = await getCollection('projects');
    if (projectsCol) {
      await projectsCol.createIndex({ conversationId: 1 });
      await projectsCol.createIndex({ status: 1 });
      if (debug) console.log('[mongoService] Indexes created for projects');
    }
    
    if (debug) console.log('[mongoService] Creating indexes for conversations');
    const convCol = await getCollection('conversations');
    if (convCol) {
      await convCol.createIndex({ conversationId: 1 });
      await convCol.createIndex({ appId: 1 });
      if (debug) console.log('[mongoService] Indexes created for conversations');
    }
    
    if (debug) console.log('[mongoService] Creating indexes for messages');
    const msgCol = await getCollection('messages');
    if (msgCol) {
      await msgCol.createIndex({ conversationId: 1 });
      await msgCol.createIndex({ appId: 1, timestamp: 1 });
      if (debug) console.log('[mongoService] Indexes created for messages');
    }
  } catch (e) {
    console.error('[mongoService] ensureIndexes error:', { message: e.message, stack: e.stack });
  }
}

async function close() {
  if (debug) console.log('[mongoService] Entering close');
  if (client) {
    await client.close();
    client = null;
    db = null;
    if (debug) console.log('[mongoService] Connection closed');
  }
}

async function getCollection(name = 'messages') {
  if (debug) console.log('[mongoService] Entering getCollection', { name });
  if (!db) await connect();
  if (!db) {
    if (debug) console.log('[mongoService] No db, returning null');
    return null;
  }
  const collection = db.collection(name);
  if (debug) console.log('[mongoService] Retrieved collection', { name });
  return collection;
}

async function saveMessage(message) {
  if (debug) console.log('[mongoService] Entering saveMessage', { message });
  try {
    const doc = Object.assign({}, message, { timestamp: message.timestamp || new Date() });
    const col = await getCollection('messages');
    if (!col) {
      if (debug) console.log('[mongoService] No collection, returning doc with _id null');
      return Object.assign({ _id: null }, doc);
    }
    if (debug) console.log('[mongoService] Inserting message', { doc });
    const r = await col.insertOne(doc);
    const result = Object.assign({ _id: r.insertedId }, doc);
    console.log('[mongoService] saveMessage inserted', String(r.insertedId), 'appId=', doc.appId);
    if (debug) console.log('[mongoService] Message saved', { result });
    return result;
  } catch (e) {
    console.error('[mongoService] saveMessage error', { message: e.message, stack: e.stack });
    return Object.assign({ _id: null }, message, { timestamp: message.timestamp || new Date() });
  }
}

async function getMessages(appId = 'default-app-id', limit = 50) {
  if (debug) console.log('[mongoService] Entering getMessages', { appId, limit });
  try {
    const col = await getCollection('messages');
    if (!col) return [];
    const cursor = col.find({ appId }).sort({ timestamp: 1 }).limit(limit);
    const docs = await cursor.toArray();
    if (debug) console.log('[mongoService] Retrieved messages', { count: docs.length });
    return docs;
  } catch (e) {
    console.error('[mongoService] getMessages error', { appId, message: e.message, stack: e.stack });
    return [];
  }
}

async function getMessagesByConversation(conversationId, limit = 200) {
  if (debug) console.log('[mongoService] Entering getMessagesByConversation', { conversationId, limit });
  try {
    const col = await getCollection('messages');
    if (!col) return [];
    const cursor = col.find({ conversationId }).sort({ timestamp: 1 }).limit(limit);
    const docs = await cursor.toArray();
    if (debug) console.log('[mongoService] Retrieved messages by conversation', { count: docs.length });
    return docs;
  } catch (e) {
    console.error('[mongoService] getMessagesByConversation error', { conversationId, message: e.message, stack: e.stack });
    return [];
  }
}

async function getSetting(key) {
  if (debug) console.log('[mongoService] Entering getSetting', { key });
  try {
    const col = await getCollection('settings');
    if (!col) return null;
    const doc = await col.findOne({ key });
    if (debug) console.log('[mongoService] Retrieved setting', { value: doc?.value });
    return doc ? doc.value : null;
  } catch (e) {
    console.error('[mongoService] getSetting error', { key, message: e.message, stack: e.stack });
    return null;
  }
}

async function setSetting(key, value) {
  if (debug) console.log('[mongoService] Entering setSetting', { key, value });
  try {
    const col = await getCollection('settings');
    if (!col) return null;
    await col.updateOne({ key }, { $set: { key, value, updatedAt: new Date() } }, { upsert: true });
    if (debug) console.log('[mongoService] Setting updated');
    return value;
  } catch (e) {
    console.error('[mongoService] setSetting error', { key, message: e.message, stack: e.stack });
    return null;
  }
}

async function saveConversation(conv) {
  if (debug) console.log('[mongoService] Entering saveConversation', { conv });
  try {
    if (!conv) return null;
    const { appId = 'default-app-id', conversationId, title = '', meta = {} } = conv;
    if (!conversationId) return null;
    const col = await getCollection('conversations');
    if (!col) return null;
    const doc = { appId, conversationId, title: title || '', meta: meta || {}, updatedAt: new Date() };
    await col.updateOne({ conversationId }, { $set: doc }, { upsert: true });
    const saved = await col.findOne({ conversationId });
    if (debug) console.log('[mongoService] Conversation saved', { saved });
    return saved;
  } catch (e) {
    console.error('[mongoService] saveConversation error', { conversationId: conv?.conversationId, message: e.message, stack: e.stack });
    return null;
  }
}

async function getConversation(conversationId) {
  if (debug) console.log('[mongoService] Entering getConversation', { conversationId });
  try {
    if (!conversationId) return null;
    const col = await getCollection('conversations');
    if (!col) return null;
    const conv = await col.findOne({ conversationId });
    if (debug) console.log('[mongoService] Retrieved conversation', { conv });
    return conv;
  } catch (e) {
    console.error('[mongoService] getConversation error', { conversationId, message: e.message, stack: e.stack });
    return null;
  }
}

async function searchConversations(appId = 'default-app-id', query = '', limit = 50) {
  if (debug) console.log('[mongoService] Entering searchConversations', { appId, query, limit });
  try {
    const col = await getCollection('conversations');
    if (!col) return [];
    const q = { appId };
    if (query && query.length) q.title = { $regex: query, $options: 'i' };
    const docs = await col.find(q).sort({ updatedAt: -1 }).limit(Number(limit)).toArray();
    if (debug) console.log('[mongoService] Retrieved conversations', { count: docs.length });
    return docs;
  } catch (e) {
    console.error('[mongoService] searchConversations error', { appId, query, message: e.message, stack: e.stack });
    return [];
  }
}

async function getGoals() {
  if (debug) console.log('[mongoService] Entering getGoals');
  try {
    const col = await getCollection('goals');
    if (!col) return [];
    const goals = await col.find({}).toArray();
    if (debug) console.log('[mongoService] Retrieved goals', { count: goals.length });
    return goals;
  } catch (e) {
    console.error('[mongoService] getGoals error', { message: e.message, stack: e.stack });
    return [];
  }
}

async function getProjectGoal(projectId) {
    if (debug) console.log('[mongoService] Entering getProjectGoal', { projectId });
    try {
        const col = await getCollection('goals');
        if (!col) return null;
        const goal = await col.findOne({ projectId });
        if (debug) console.log('[mongoService] Retrieved projectGoal', { goal });
        return goal;
    } catch (e) {
        console.error('[mongoService] getProjectGoal error', { projectId, message: e.message, stack: e.stack });
        return null;
    }
}

async function createProject(sessionId, projectData) {
  if (debug) console.log('[mongoService] Entering createProject', { sessionId, projectData });
  try {
    const col = await getCollection('projects');
    if (!col) return null;
    const doc = {
      ...projectData,
      conversationId: sessionId,
      createdAt: new Date(),
      status: 'in-progress',
      currentPersonaIndex: 0,
      currentTaskIndex: 0
    };
    const r = await col.insertOne(doc);
    console.log('[mongoService] createProject inserted', String(r.insertedId));
    const created = await col.findOne({ _id: r.insertedId });
    if (debug) console.log('[mongoService] Project created', { created });
    return created;
  } catch (e) {
    console.error('[mongoService] createProject error', { sessionId, message: e.message, stack: e.stack });
    return null;
  }
}

async function getProject(sessionId) {
  if (debug) console.log('[mongoService] Entering getProject', { sessionId });
  try {
    const col = await getCollection('projects');
    if (!col) return null;
    const project = await col.findOne({ conversationId: sessionId });
    if (debug) console.log('[mongoService] Retrieved project', { project });
    return project;
  } catch (e) {
    console.error('[mongoService] getProject error', { sessionId, message: e.message, stack: e.stack });
    return null;
  }
}

async function updateProject(sessionId, updateData) {
  if (debug) console.log('[mongoService] Entering updateProject', { sessionId, updateData });
  try {
    const col = await getCollection('projects');
    if (!col) return null;
    await col.updateOne({ conversationId: sessionId }, { $set: { ...updateData, updatedAt: new Date() } });
    console.log('[mongoService] updateProject updated project for conversationId', sessionId);
    const updated = await col.findOne({ conversationId: sessionId });
    if (debug) console.log('[mongoService] Updated project', { updated });
    return updated;
  } catch (e) {
    console.error('[mongoService] updateProject error', { sessionId, message: e.message, stack: e.stack });
    return null;
  }
}

module.exports = {
  connect,
  close,
  saveMessage,
  getMessages,
  getCollection,
  getMessagesByConversation,
  getSetting,
  setSetting,
  saveConversation,
  getConversation,
  searchConversations,
  getGoals,
  getProjectGoal,
  createProject,
  getProject,
  updateProject
};