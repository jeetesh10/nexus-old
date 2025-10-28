// config.js
// Centralized configuration loader

require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });

module.exports = {
  PORT: process.env.PORT || 4000, // Updated to 4000 to match your configuration
  NODE_ENV: process.env.NODE_ENV || 'development',
  OPENAI_API_KEY: process.env.OPENAI_API_KEY || '',
  MONGO_URI: process.env.MONGO_URI || '',
  MONGO_DB_NAME: process.env.MONGO_DB_NAME || 'MyBot',
  GEMINI_API_KEY: process.env.GEMINI_API_KEY || process.env.GEMINI_apiKey || '',
  GROQ_API_KEY: process.env.GROQ_API_KEY || process.env.GROQ_apiKey || process.env.GROQ_APIKEY || '',
  GROQ_API_URL: process.env.GROQ_API_URL || process.env.GROQ_URL || '',
  LLM_ROLE_MAP: (process.env.LLM_ROLE_MAP || 'primary:gemini,reviewer:groq')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean)
    .reduce((acc, pair) => {
      const [role, svc] = pair.split(':').map(x => x && x.trim());
      if (role && svc) acc[role] = svc;
      return acc;
    }, {}),
  LLM_ORCHESTRATOR_ORDER: (process.env.LLM_ORCHESTRATOR_ORDER || 'primary,reviewer,primary')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean)
};