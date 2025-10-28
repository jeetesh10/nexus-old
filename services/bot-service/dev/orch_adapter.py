from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
import httpx

app = FastAPI(title="Orchestrator Compatibility Adapter")

REAL_ORCH = "http://127.0.0.1:8080"  # real orchestrator service


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


@app.post("/api/mongodb/operation")
async def operation(payload: OpPayload):
    coll = payload.collection or "default"
    async with httpx.AsyncClient(timeout=10.0) as client:
        if payload.action == "find_one":
            q = {"filter": payload.filter or {}, "limit": 1}
            r = await client.post(f"{REAL_ORCH}/{coll}/query", json=q)
            r.raise_for_status()
            data = r.json()
            results = data.get("results", [])
            return {"ok": True, "result": (results[0] if results else None)}

        if payload.action == "find":
            q = {"filter": payload.filter or {}, "limit": payload.limit or 100}
            if payload.sort:
                # convert sort dict to list of lists
                q["sort"] = [[k, v] for k, v in (payload.sort or {}).items()]
            r = await client.post(f"{REAL_ORCH}/{coll}/query", json=q)
            r.raise_for_status()
            data = r.json()
            return {"ok": True, "result": data.get("results", [])}

        if payload.action == "insert_one":
            doc = payload.document or {}
            r = await client.post(f"{REAL_ORCH}/{coll}", json={"data": doc})
            r.raise_for_status()
            created = r.json()
            new_id = created.get("id")
            if new_id:
                # fetch full doc
                r2 = await client.get(f"{REAL_ORCH}/{coll}/{new_id}")
                r2.raise_for_status()
                doc_out = r2.json().get("document")
                return {"ok": True, "result": doc_out}
            return {"ok": True, "result": None}

        if payload.action == "update_one":
            # find doc by filter, update with $set
            filt = payload.filter or {}
            q = {"filter": filt, "limit": 1}
            r = await client.post(f"{REAL_ORCH}/{coll}/query", json=q)
            r.raise_for_status()
            results = r.json().get("results", [])
            if not results:
                return {"ok": True, "result": None}
            doc = results[0]
            doc_id = doc.get("id") or doc.get("_id")
            if not doc_id:
                return {"ok": True, "result": None}
            # apply $set
            upd = payload.update or {}
            set_fields = upd.get("$set", {}) if isinstance(upd, dict) else {}
            r2 = await client.put(f"{REAL_ORCH}/{coll}/{doc_id}", json={"data": set_fields})
            r2.raise_for_status()
            return {"ok": True, "result": r2.json().get("document")}

        raise HTTPException(status_code=400, detail=f"unsupported action: {payload.action}")
