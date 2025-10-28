import os
import pytest
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
os.environ["SKIP_ORCH_HEALTH"] = "1"
from httpx import AsyncClient, ASGITransport
from smartcart_bot.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"
