# Mybot

A small LangChain-style chatbot skeleton named Mybot. This repo provides a minimal structure for building conversational chains, LLM and vector DB adapters, and an Express-based HTTP API.

Quick start
1. Copy `.env` and set your keys.
2. npm install
3. npm start

Project structure
- src/ - application code
  - chains/ - conversational chains
  - services/ - llm + vector db adapters
  - api/ - express routes

Notes
- The service implementations are stubs; replace `llmService` and `vectorDbService` with real adapters (OpenAI/langchain, Chroma/Pinecone).

Configuration & environment
- Create a `.env` file at the repository root or set environment variables in your environment.
- Important variables:
  - `PORT` - HTTP port (default: 3000)
  - `MONGO_URI` - MongoDB connection string (optional). When set, the service will attempt to connect on startup and will exit if the connection fails.
  - `MONGO_DB_NAME` - Mongo database name (default: MyBot)
  - `OPENAI_API_KEY` - optional fallback key for LLM usage
  - `GEMINI_API_KEY` - preferred key for the included Gemini LLM adapter

HTTP endpoints
- `POST /api/chat` - dispatches chat commands; body example: { type: 'greeting' | 'summarize' | undefined, input: { text/query }, user: { name } }
- `POST /api/messages` - save a user message and get an AI reply; body example: { appId, text, userId }
- `GET /api/messages` - fetch saved messages for an appId (query params: appId, limit)
- `GET /api/debug` - returns recent logs (no auth - avoid enabling in production)

Notes on behavior
- Mongo: if `MONGO_URI` is not provided the `mongoService` becomes a no-op (it logs a warning). If `MONGO_URI` is provided the server will attempt to connect during startup and exit on fatal connection errors.
- LLM: `src/services/llmService.js` exports `generate(prompt, opts)` which returns `{ text, raw }`. A backwards-compatible `getAIResponse(prompt)` wrapper returns the plain text.

Security
- Do not commit `.env` or secrets. The debug endpoint is unauthenticated by default; protect or disable it for production.
