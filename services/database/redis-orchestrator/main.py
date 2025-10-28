from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from typing import Any, Optional, Dict, TYPE_CHECKING

import aioredis

if TYPE_CHECKING:
    # provide a type alias for linters and type-checkers
    from aioredis import Redis as _Redis
    RedisType = _Redis
else:
    RedisType = Any

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis.default.svc.cluster.local:6379")

class Op(BaseModel):
    action: str
    key: str
    value: Optional[str] = None

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/api/redis/operation")
async def op(payload: Op) -> Dict[str, Any]:
    # aioredis.from_url returns an async Redis client
    redis: "RedisType" = await aioredis.from_url(REDIS_URL)
    if payload.action == "get":
        val = await redis.get(payload.key)
        # val is bytes | None
        result: Optional[str]
        if val is None:
            result = None
        else:
            # decode bytes to str
            result = val.decode()
        return {"ok": True, "result": result}
    elif payload.action == "set":
        if payload.value is None:
            raise HTTPException(status_code=400, detail="missing value for set")
        await redis.set(payload.key, payload.value)
        return {"ok": True}
    else:
        raise HTTPException(status_code=400, detail="unknown action")
