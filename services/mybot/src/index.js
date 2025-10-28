// src/index.js - app entrypoint
const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const cors = require('cors');
const config = require('../config/config');
const chatRoutes = require('./api/chatRoutes');
const debugRoutes = require('./api/debugRoutes');
// Attempt early mongo connect to surface connection errors at startup
const mongo = require('./services/mongoService');

// If a Mongo URI is configured, attempt a blocking connect during startup so
// connection problems surface immediately. If not configured, mongoService
// will behave as a no-op and the server will start without DB backing.
const hasMongo = Boolean(config.MONGO_URI);
if (hasMongo) {
  console.log('MONGO_URI configured; connecting to MongoDB before starting server...');
} else {
  console.log('MONGO_URI not configured; starting without DB (mongoService no-op).');
}

async function start() {
  if (hasMongo) {
    try {
      await mongo.connect();
    } catch (err) {
      console.error('mongo.connect error:', err && err.message);
      // Fail fast if Mongo is required and cannot connect
      process.exit(1);
    }
  } else {
    // attempt connect but don't fail if missing
    mongo.connect().catch(err => console.warn('mongo.connect (non-blocking) error:', err && err.message));
  }

  const app = express();
  app.use(cors());
  app.use(bodyParser.json());

  // Serve API
  app.use('/api', chatRoutes);
  app.use('/api/debug', debugRoutes);

  // Serve static UI from public/
  const publicDir = path.resolve(__dirname, '..', 'public');
  app.use(express.static(publicDir));

  // Fallback to index.html for SPA
  app.get('*', (req, res) => {
    res.sendFile(path.join(publicDir, 'index.html'));
  });

  const port = config.PORT || 4000;
  app.listen(port, () => {
    console.log(`Mybot listening on port ${port}`);
  });
}

start();