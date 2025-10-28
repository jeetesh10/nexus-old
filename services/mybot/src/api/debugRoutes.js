// src/api/debugRoutes.js
const express = require('express');
const fs = require('fs');
const path = require('path');
const router = express.Router();
const mongo = require('../services/mongoService');

// Path to the app log file (adjust if you write logs elsewhere)
const LOG_PATH = path.join(process.cwd(), 'mybot.log');

// Return raw log text and conversation debug data. Consider adding auth in prod.
router.get('/', async (req, res) => {
  try {
    let logContent = '(log file not found)';
    if (fs.existsSync(LOG_PATH)) {
      const stat = fs.statSync(LOG_PATH);
      const maxBytes = 200 * 1024; // 200 KB
      let start = 0;
      if (stat.size > maxBytes) start = stat.size - maxBytes;
      const fd = fs.openSync(LOG_PATH, 'r');
      const buffer = Buffer.alloc(stat.size - start);
      fs.readSync(fd, buffer, 0, buffer.length, start);
      fs.closeSync(fd);
      logContent = buffer.toString('utf8');
    }

    // Fetch recent conversations with orchestration data
    const conversations = await mongo.getCollection('messages');
    const recentMessages = await conversations.find({}).sort({ timestamp: -1 }).limit(10).toArray();
    let debugData = recentMessages.map(msg => ({
      _id: msg._id,
      appId: msg.appId,
      conversationId: msg.conversationId,
      userId: msg.userId,
      role: msg.role,
      text: msg.text,
      timestamp: msg.timestamp,
      orchestration: msg.orchestration || {},
      meta: msg.meta || {}
    })).reverse(); // Reverse to show oldest first

    res.status(200).type('application/json').json({
      log: logContent,
      conversations: debugData
    });
  } catch (err) {
    console.error('debugRoutes error', err);
    res.status(500).type('application/json').json({ error: 'error_reading_data', detail: err.message });
  }
});

module.exports = router;