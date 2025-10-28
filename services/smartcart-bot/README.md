# SmartCart Bot Service

Python FastAPI service for SmartCartBot, using the MongoDB Orchestrator HTTP façade for persistence.

- Port: 8087 (see `config/ports.yaml` → `smartcart-bot`)
- Health: `GET /health`
- Sample API: `POST /api/v1/smartcart/session` to upsert user session preferences

## Configuration
Env vars (see `.env.example`):
- `PORT` (default 8087)
- `MONGODB_ORCHESTRATOR_URL` (in-cluster default points to `mongodb-orchestrator`)
- `MONGODB_DATABASE` (default `nexus`)
- `SKIP_ORCH_HEALTH` (set `1` to skip orchestrator health check in local tests)

## Run locally
1. Install deps
	- `pip install -r requirements.txt`
2. Start
	- `uvicorn smartcart_bot.main:app --host 0.0.0.0 --port 8087`

## Container
The Dockerfile exposes 8087 and starts `uvicorn`.

## Kubernetes (conceptual)
See `iac/kubernetes/*` for deployment and service. Ensure ports match `config/ports.yaml`.

## API
- `GET /health` → `{ status: "ok", env: "dev" }`
- `POST /api/v1/smartcart/session` body:
  ```json
  {"user_id":"u1", "session_id":"s1", "preferences": {"currency":"USD"}}
  ```
  Response: `{ "ok": true, "action": "inserted|updated" }`
