# Nexus BotService — README

🎯 Summary
- Purpose: FastAPI microservice exposing `/api/v1/bot/chat` with a pluggable model layer (Gemini, Groq).
- Integration: Uses a MongoDB Orchestrator HTTP adapter (MongoOrchestratorClient) for config and persistence.
- Model calls: Provider stubs exist (synchronous); blocking invocations are run off the event loop.

✨ Visual status markers
- ✅ Done
- ⚠️ In-progress / Partial
- ❌ Not started
- 🚧 Action required / Next steps

📦 What is done ✅
- Project scaffold: `services/bot-service`
- Async FastAPI app lifecycle and chat endpoint
- Pydantic models: `src/app/models.py`
- Config loader: `src/app/core/config.py` (.env support)
- MongoDB Orchestrator HTTP adapter: `src/app/core/mongo_orchestrator_client.py`
- Async LLM manager (adapter): `src/app/core/llm_manager.py`
- Conversation persistence: `src/app/core/conversation_manager.py`
- Orchestrator flow: `src/app/core/orchestrator.py`
- Model service stubs: `src/app/services/{gemini,groq}_service.py`
- Dev seed script: `scripts/seed_db.py` (direct DB)
- Requirements: `requirements.txt` (includes httpx)

⚠️ In-progress / Partial
- Seed flow: seed script uses direct DB (pymongo). Consider seeding via orchestrator API or ensure credentials.
- Docker / docker-compose: suggested, not finalized in repo.
- Model SDKs: provider implementations are placeholders.

❌ Remaining (high priority)
1. Replace stubs with production SDK calls (Gemini + Groq).  
2. Decide and implement seeding approach (orchestrator API vs direct DB).  
3. Add Dockerfile + `docker-compose.dev.yml` and validate local stack (mongo + orchestrator + bot-service).  
4. Add unit/integration tests and CI pipeline.  
5. Add JWT / API gateway plan (Keycloak / APISIX) if exposing externally.  
6. Kubernetes manifests, Linkerd ServiceProfile, RBAC, and observability (Prometheus, logs).

🚧 Quick dev run (pick depending on seeding choice)
1) create env & install
```bash
cd /workspaces/nexus/services/bot-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set MONGODB_ORCHESTRATOR_URL or MONGO_DB_URL in .env depending on integration
```

2) seed
- If direct DB access available:
```bash
python scripts/seed_db.py
```
- If using MongoDB Orchestrator, run an orchestrator-seed script (TODO) or call orchestrator API.

3) run service
```bash
uvicorn src.app.main:app --reload --port 8085
curl -sS -X POST http://localhost:8085/api/v1/bot/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","session_id":"s1","message":"hello"}' | jq
```

🔧 Immediate recommended next tasks (choose one)
- A — Implement Gemini + Groq SDKs (priority).  
- B — Commit Dockerfile + docker-compose; bring up local stack and adapt ports to avoid conflicts.  
- C — Update `scripts/seed_db.py` to seed via the Mongo Orchestrator HTTP API.

📝 Notes & small fixes
- Add `MONGODB_ORCHESTRATOR_URL` to `.env.example` and `src/app/core/config.py`.
- `requirements.txt` already includes `httpx`; ensure virtualenv is active in VS Code so Pylance finds packages.
- Convert seed timestamps to timezone-aware datetimes (use datetime.now(timezone.utc).isoformat()).

📌 Keep this README / `STATUS.md` updated as tasks progress.
