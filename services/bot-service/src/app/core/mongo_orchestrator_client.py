from typing import Any, Dict, List, Optional
import httpx

class MongoOrchestratorClient:
    """
    Thin async adapter for the MongoDB Orchestrator HTTP API.
    Provides simple helpers used by the service:
      - find_one(collection, filter)
      - insert_one(collection, doc)
      - update_one(collection, filter, update)
      - find(collection, filter, sort=None, limit=None) -> list
    Implementation expects the orchestrator to expose a POST /api/mongodb/operation
    that accepts JSON payloads like:
      { "action":"find_one", "database":"nexus", "collection":"models", "filter": {...} }
    and returns JSON { "ok": true, "result": <...> } or raises HTTP error.
    Adapt the payload/paths to your orchestrator API if different.
    """
    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None, database: str = "nexus"):
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
        payload: Dict[str, Any] = {"action": "update_one", "database": self.database, "collection": collection, "filter": filter, "update": update}
        res = await self._op(payload)
        return res.get("result")

    async def find(self, collection: str, filter: Dict[str, Any], sort: Dict[str, Any] | None = None, limit: int | None = None) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"action": "find", "database": self.database, "collection": collection, "filter": filter}
        if sort is not None:
            payload["sort"] = sort
        if limit is not None:
            payload["limit"] = limit
        res = await self._op(payload)
        return res.get("result", [])