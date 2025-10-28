from __future__ import annotations
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Any, Optional, AsyncGenerator, Dict

import httpx
from fastapi import FastAPI, HTTPException

from .models import ChatRequest, ChatResponse
from .core.config import settings
from .core.mongo_orchestrator_client import MongoOrchestratorClient
from .core.llm_manager import AsyncLLMManager
from .core.conversation_manager import ConversationManager
from .core.orchestrator import Orchestrator

logger = logging.getLogger("bot-service")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # initialize state attributes without deprecated type comments
    app.state._httpx_client = None
    app.state.mongo_orch_client = None
    app.state.llm_manager = None
    app.state.convo_manager = None
    app.state.orchestrator = None

    client = httpx.AsyncClient(timeout=10.0)
    app.state._httpx_client = client

    orch_url = getattr(settings, "MONGODB_ORCHESTRATOR_URL", "http://127.0.0.1:8001")
    app.state.mongo_orch_client = MongoOrchestratorClient(base_url=orch_url, client=client)

    healthy = False
    for attempt in range(5):
        try:
            await app.state.mongo_orch_client.health()
            healthy = True
            logger.info("Connected to MongoOrchestrator at %s", orch_url)
            break
        except Exception as ex:
            wait = min(2 ** attempt, 10)
            logger.warning("Orchestrator health check failed (attempt %d/%d): %s — retrying in %ds", attempt + 1, 5, str(ex), wait)
            await asyncio.sleep(wait)

    if not healthy:
        logger.error("MongoOrchestrator not reachable at %s after retries; aborting startup", orch_url)
        raise RuntimeError("MongoOrchestrator unreachable")

    app.state.llm_manager = AsyncLLMManager(app.state.mongo_orch_client, http_client=client)
    app.state.convo_manager = ConversationManager(app.state.mongo_orch_client)
    app.state.orchestrator = Orchestrator(app.state.llm_manager, app.state.convo_manager)

    try:
        yield
    finally:
        if app.state._httpx_client:
            await app.state._httpx_client.aclose()


app = FastAPI(title="Nexus BotService", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "env": getattr(settings, "ENV", "dev")}


@app.post("/api/v1/bot/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    from typing import cast
    orch: Optional[Orchestrator] = cast(Optional[Orchestrator], app.state.orchestrator)
    if orch is None:
        raise HTTPException(status_code=503, detail="service unavailable")

    try:
        out: Dict[str, Any] = await orch.process_request(req.user_id, req.session_id, req.message, req.goal_id)
        return ChatResponse(**out)
    except Exception:
        logger.exception("Error processing chat request")
        raise HTTPException(status_code=500, detail="internal server error")
