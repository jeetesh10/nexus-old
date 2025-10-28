Redis Orchestrator: small HTTP façade for Redis GET/SET used by services that want a simple HTTP-backed cache interface.

Endpoints:
- GET /health
- POST /api/redis/operation { action: "get"|"set", key: "k", value?: "v" }

This is intentionally minimal for local testing.