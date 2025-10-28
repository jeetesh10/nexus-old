import os
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
import motor.motor_asyncio
from bson.objectid import ObjectId
from bson.errors import InvalidId
from contextlib import asynccontextmanager

LOG = logging.getLogger("mongo-orchestrator")
logging.basicConfig(level=logging.INFO)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "nexus")
SERVICE_PORT = int(os.getenv("PORT", "8080"))

app = FastAPI(
    title="MongoDB Orchestrator",
    version="0.1.0",
    description="A small orchestrator that exposes generic CRUD and query endpoints for MongoDB. Use /docs for Swagger UI.",
)

# Allow other services to call this orchestrator
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Typed globals
client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None


class DocumentIn(BaseModel):
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw document to insert. Should be a JSON object.",
        example={"name": "alice", "age": 30},
    )


class DocumentUpdate(BaseModel):
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Fields to set on the document (applies $set).",
        example={"age": 31},
    )


class DocumentOut(BaseModel):
    id: str
    document: Dict[str, Any]


class CreateResponse(BaseModel):
    id: str


class QueryRequest(BaseModel):
    filter: Dict[str, Any] = Field(default_factory=dict, example={"age": {"$gte": 18}})
    projection: Optional[Dict[str, int]] = Field(
        default=None, example={"name": 1, "_id": 0}
    )
    limit: int = Field(default=100, example=25)
    skip: int = Field(default=0, example=0)
    sort: Optional[List[List[Any]]] = Field(
        default=None, example=[["age", -1]]
    )  # e.g. [["field", 1], ["other", -1]]


def oid_to_str(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Return a shallow copy with _id -> id (string)."""
    if not doc:
        return doc
    out = dict(doc)
    _id = out.pop("_id", None)
    if _id is not None:
        out["id"] = str(_id)
    return out


def normalize_bson(obj: Any) -> Any:
    """
    Convert BSON types (ObjectId, nested lists/dicts) to JSON-serializable Python types.
    """
    from bson import ObjectId  # local import for safety

    if obj is None:
        return None
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: normalize_bson(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_bson(v) for v in obj]
    # leave other primitives as-is
    return obj


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db
    LOG.info("Starting MongoDB orchestrator lifespan: connecting to %s", MONGO_URI)
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    try:
        await client.admin.command("ping")
        LOG.info("Connected to MongoDB database=%s", MONGO_DB)
    except Exception as e:
        LOG.exception("MongoDB ping failed during startup: %s", e)
        # allow startup to complete; endpoints will return 503 if DB unavailable
    try:
        yield
    finally:
        if client:
            client.close()
            LOG.info("MongoDB connection closed")


app.router.lifespan_context = lifespan  # type: ignore[attr-defined]


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to the Swagger UI."""
    return RedirectResponse(url="/docs")


@app.get("/health", status_code=status.HTTP_200_OK, tags=["admin"])
async def health():
    """Health endpoint — checks MongoDB ping."""
    if client is None:
        raise HTTPException(status_code=503, detail="MongoDB client not initialized")
    try:
        await client.admin.command("ping")
        return {"status": "ok"}
    except Exception as e:
        LOG.warning("Health check failed: %s", e)
        raise HTTPException(status_code=503, detail="MongoDB unreachable")


@app.get("/collections", tags=["admin"])
async def list_collections():
    """List collection names in the configured DB."""
    if db is None:
        raise HTTPException(status_code=503, detail="database not available")
    names = await db.list_collection_names()
    return {"collections": names}


@app.post("/{collection}", status_code=status.HTTP_201_CREATED, response_model=CreateResponse, tags=["documents"])
async def create_document(collection: str, doc_in: DocumentIn):
    """Insert a document into the named collection. Returns new id."""
    if db is None:
        raise HTTPException(status_code=503, detail="database not available")
    res = await db[collection].insert_one(doc_in.data)
    return {"id": str(res.inserted_id)}


@app.get("/{collection}/{doc_id}", response_model=DocumentOut, tags=["documents"])
async def get_document(collection: str, doc_id: str):
    """Get a single document by id."""
    if db is None:
        raise HTTPException(status_code=503, detail="database not available")
    try:
        _id = ObjectId(doc_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="invalid document id")
    doc = await db[collection].find_one({"_id": _id})
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    # normalize BSON types before returning
    return {"id": str(_id), "document": normalize_bson(doc)}


@app.put("/{collection}/{doc_id}", response_model=DocumentOut, tags=["documents"])
async def update_document(collection: str, doc_id: str, update: DocumentUpdate):
    """Update fields on a document and return the updated document."""
    if db is None:
        raise HTTPException(status_code=503, detail="database not available")
    try:
        _id = ObjectId(doc_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="invalid document id")
    res = await db[collection].update_one({"_id": _id}, {"$set": update.data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="document not found")
    doc = await db[collection].find_one({"_id": _id})
    return {"id": str(_id), "document": normalize_bson(doc)}


@app.delete("/{collection}/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["documents"])
async def delete_document(collection: str, doc_id: str):
    """Delete a document."""
    if db is None:
        raise HTTPException(status_code=503, detail="database not available")
    try:
        _id = ObjectId(doc_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="invalid document id")
    res = await db[collection].delete_one({"_id": _id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="document not found")
    return {}


@app.post("/{collection}/query", tags=["documents"])
async def query_documents(collection: str, q: QueryRequest):
    """Run a query with pagination/sort/projection and return results."""
    if db is None:
        raise HTTPException(status_code=503, detail="database not available")
    cursor = db[collection].find(q.filter, q.projection)
    if q.sort:
        try:
            cursor = cursor.sort(q.sort)
        except Exception as e:
            LOG.warning("Invalid sort specification: %s", e)
            raise HTTPException(status_code=400, detail="invalid sort specification")
    if q.skip:
        cursor = cursor.skip(q.skip)
    if q.limit:
        cursor = cursor.limit(q.limit)
    results: List[Dict[str, Any]] = []
    async for doc in cursor:
        results.append(normalize_bson(doc))
    return {"results": results, "count": len(results)}


@app.get("/info", tags=["admin"])
async def info():
    """Admin info: DB name and URI used (URI sanitized in logs)."""
    return {"db": MONGO_DB, "uri": MONGO_URI, "status": "running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=SERVICE_PORT, log_level="info")