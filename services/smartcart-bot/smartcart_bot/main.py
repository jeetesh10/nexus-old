from __future__ import annotations
import asyncio
import logging
from contextlib import asynccontextmanager
import os
from typing import Any, Dict, Optional, AsyncGenerator

import httpx
from fastapi import FastAPI
from pydantic import BaseModel


logger = logging.getLogger("smartcart-bot")
logging.basicConfig(level=logging.INFO)


class Settings(BaseModel):
	ENV: str = os.getenv("ENV", "dev")
	PORT: int = int(os.getenv("PORT", "8087"))
	MONGODB_ORCHESTRATOR_URL: str = os.getenv(
		"MONGODB_ORCHESTRATOR_URL",
		# Use the ClusterIP Service port (80) exposed by mongodb-orchestrator
		# Avoid targeting the backend container port (8080) directly, which breaks service routing/linkerd
		"http://mongodb-orchestrator.default.svc.cluster.local",
	)
	MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "nexus")
	SKIP_ORCH_HEALTH: bool = os.getenv("SKIP_ORCH_HEALTH", "0") in {"1", "true", "TRUE"}


settings = Settings()


class MongoOrchestratorClient:
	def __init__(self, base_url: str, client: httpx.AsyncClient | None = None, database: str = "nexus") -> None:
		self.base_url = base_url.rstrip("/")
		self._client = client or httpx.AsyncClient(timeout=10.0)
		self.database = database

	async def health(self) -> Dict[str, Any]:
		r = await self._client.get(f"{self.base_url}/health")
		r.raise_for_status()
		return r.json()

	async def _op(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		url = f"{self.base_url}/api/mongodb/operation"
		r = await self._client.post(url, json=payload)
		r.raise_for_status()
		return r.json()

	async def find_one(self, collection: str, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		payload: Dict[str, Any] = {"action": "find_one", "database": self.database, "collection": collection, "filter": filter}
		res = await self._op(payload)
		return res.get("result")

	async def insert_one(self, collection: str, doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		payload: Dict[str, Any] = {"action": "insert_one", "database": self.database, "collection": collection, "document": doc}
		res = await self._op(payload)
		return res.get("result")

	async def update_one(self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		payload: Dict[str, Any] = {
			"action": "update_one",
			"database": self.database,
			"collection": collection,
			"filter": filter,
			"update": update,
		}
		res = await self._op(payload)
		return res.get("result")


class SessionUpsertRequest(BaseModel):
	user_id: str
	session_id: str
	preferences: Dict[str, Any] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
	app.state._httpx_client = httpx.AsyncClient(timeout=10.0)
	orch_url = settings.MONGODB_ORCHESTRATOR_URL
	app.state.mongo_orch = MongoOrchestratorClient(orch_url, client=app.state._httpx_client, database=settings.MONGODB_DATABASE)

	healthy = False
	if settings.SKIP_ORCH_HEALTH:
		logger.info("Skipping MongoOrchestrator health check (SKIP_ORCH_HEALTH=1)")
		healthy = True
	else:
		for attempt in range(5):
			try:
				await app.state.mongo_orch.health()
				healthy = True
				logger.info("Connected to MongoOrchestrator at %s", orch_url)
				break
			except Exception as ex:
				wait = min(2 ** attempt, 10)
				logger.warning(
					"Orchestrator health check failed (attempt %d/%d): %s — retrying in %ds",
					attempt + 1,
					5,
					str(ex),
					wait,
				)
				await asyncio.sleep(wait)

		if not healthy:
			logger.error("MongoOrchestrator not reachable at %s after retries; aborting startup", orch_url)
			raise RuntimeError("MongoOrchestrator unreachable")

	try:
		yield
	finally:
		try:
			await app.state._httpx_client.aclose()
		except Exception:
			pass


app = FastAPI(title="SmartCart Bot", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> Dict[str, str]:
	return {"status": "ok", "env": settings.ENV}


@app.post("/api/v1/smartcart/session")
async def upsert_session(req: SessionUpsertRequest) -> Dict[str, Any]:
	"""
	Create or update a user's session preferences document via MongoOrchestrator.
	Collection: smartcart_sessions
	Key: { user_id, session_id }
	"""
	mongo: MongoOrchestratorClient = app.state.mongo_orch

	# Try to find existing
	existing: Optional[Dict[str, Any]] = await mongo.find_one(
		"smartcart_sessions", {"user_id": req.user_id, "session_id": req.session_id}
	)
	if existing:
		update_doc: Dict[str, Any] = {"$set": {"preferences": (req.preferences or {}), "updated_at": "now"}}
		await mongo.update_one("smartcart_sessions", {"_id": existing.get("_id")}, update_doc)
		action = "updated"
	else:
		doc: Dict[str, Any] = {
			"user_id": req.user_id,
			"session_id": req.session_id,
			"preferences": (req.preferences or {}),
			"created_at": "now",
		}
		await mongo.insert_one("smartcart_sessions", doc)
		action = "inserted"

	return {"ok": True, "action": action}
