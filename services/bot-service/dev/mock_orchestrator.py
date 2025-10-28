from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

app = FastAPI(title="Mock Mongo Orchestrator")

# simple in-memory store: {collection: [docs]}
STORE: Dict[str, List[Dict[str, Any]]] = {}
ID_COUNTER = {"_id": 1}


class OpPayload(BaseModel):
    action: str
    database: Optional[str] = None
    collection: Optional[str] = None
    filter: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None
    update: Optional[Dict[str, Any]] = None
    sort: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None


@app.get("/health")
async def health():
    return {"status": "ok"}


def _match(doc: Dict[str, Any], filt: Optional[Dict[str, Any]]) -> bool:
    if not filt:
        return True
    for k, v in filt.items():
        if k not in doc:
            return False
        if doc[k] != v:
            return False
    return True


@app.post("/api/mongodb/operation")
async def operation(payload: OpPayload):
    action = payload.action
    coll = payload.collection or "default"
    if coll not in STORE:
        STORE[coll] = []

    if action == "find_one":
        for doc in STORE[coll]:
            if _match(doc, payload.filter):
                return {"ok": True, "result": doc}
        return {"ok": True, "result": None}

    if action == "insert_one":
        doc = dict(payload.document or {})
        doc_id = ID_COUNTER["_id"]
        ID_COUNTER["_id"] += 1
        doc["_id"] = doc_id
        if "createdAt" not in doc:
            doc["createdAt"] = datetime.utcnow().isoformat()
        STORE[coll].append(doc)
        return {"ok": True, "result": doc}

    if action == "update_one":
        filt = payload.filter or {}
        upd = payload.update or {}
        for i, doc in enumerate(STORE[coll]):
            if _match(doc, filt):
                # support {$set: {...}}
                if "$set" in upd and isinstance(upd["$set"], dict):
                    for k, v in upd["$set"].items():
                        doc[k] = v
                STORE[coll][i] = doc
                return {"ok": True, "result": doc}
        return {"ok": True, "result": None}

    if action == "find":
        results = [d for d in STORE[coll] if _match(d, payload.filter)]
        # basic sort by a single key if provided
        if payload.sort:
            # sort dict like {"createdAt": 1}
            for key, direction in payload.sort.items():
                reverse = direction < 0
                results.sort(key=lambda x: x.get(key, ""), reverse=reverse)
        if payload.limit:
            results = results[: payload.limit]
        return {"ok": True, "result": results}

    raise HTTPException(status_code=400, detail=f"unsupported action: {action}")
