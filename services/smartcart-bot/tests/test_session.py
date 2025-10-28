import os
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
os.environ["SKIP_ORCH_HEALTH"] = "1"
from typing import Any, Dict
from httpx import AsyncClient, ASGITransport
from smartcart_bot.main import app


class FauxOrchestrator:
    async def health(self) -> Dict[str, Any]:
        return {"status": "ok"}

    async def find_one(self, collection: str, filter: Dict[str, Any]) -> Dict[str, Any] | None:
        return None

    async def insert_one(self, collection: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {"inserted_id": "abc"}

    async def update_one(self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        return {"matched": 1, "modified": 1}


@pytest.mark.asyncio
async def test_upsert_session_inserts(monkeypatch: Any) -> None:
    os.environ["SKIP_ORCH_HEALTH"] = "1"
    # Monkeypatch the orchestrator client on the app state
    app.state.mongo_orch = FauxOrchestrator()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload: Dict[str, Any] = {"user_id": "u1", "session_id": "s1", "preferences": {"currency": "USD"}}
        resp = await ac.post("/api/v1/smartcart/session", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        assert data.get("action") in {"inserted", "updated"}
