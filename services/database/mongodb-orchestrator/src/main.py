from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import motor.motor_asyncio
import asyncio
import logging
from datetime import datetime
import os
from auth_middleware import auth_middleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MongoDB Orchestrator Service",
    description="Orchestrated MongoDB operations for microservices",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:adminpass123@localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.nexus_platform

# Pydantic models
class DatabaseRequest(BaseModel):
    service_name: str
    database_name: str
    collection_name: str
    operation: str
    data: Optional[Dict[str, Any]] = None
    query: Optional[Dict[str, Any]] = None
    update: Optional[Dict[str, Any]] = None

class DatabaseResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: str
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    mongodb_connected: bool
    timestamp: datetime

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        await client.admin.command('ping')
        mongodb_connected = True
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        mongodb_connected = False
    
    return HealthResponse(
        status="healthy" if mongodb_connected else "unhealthy",
        mongodb_connected=mongodb_connected,
        timestamp=datetime.utcnow()
    )

@app.post("/api/mongodb/operation", response_model=DatabaseResponse)
async def mongodb_operation(request: DatabaseRequest, user_info: Dict[str, Any] = Depends(auth_middleware.require_auth)):
    """Generic MongoDB operation endpoint"""
    try:
        # Check if user has access to the requested service
        await auth_middleware.get_user_service_access(service_name=request.service_name)
        
        # Get service-specific database
        service_db = client[f"{request.service_name}_{request.database_name}"]
        collection = service_db[request.collection_name]
        
        result = None
        
        if request.operation == "insert":
            if request.data:
                result = await collection.insert_one(request.data)
                result = {"inserted_id": str(result.inserted_id)}
            else:
                raise HTTPException(status_code=400, detail="Data required for insert operation")
                
        elif request.operation == "find":
            query = request.query or {}
            cursor = collection.find(query)
            result = await cursor.to_list(length=1000)
            
        elif request.operation == "find_one":
            query = request.query or {}
            result = await collection.find_one(query)
            
        elif request.operation == "update":
            if request.query and request.update:
                result = await collection.update_many(request.query, request.update)
                result = {"modified_count": result.modified_count}
            else:
                raise HTTPException(status_code=400, detail="Query and update required for update operation")
                
        elif request.operation == "delete":
            if request.query:
                result = await collection.delete_many(request.query)
                result = {"deleted_count": result.deleted_count}
            else:
                raise HTTPException(status_code=400, detail="Query required for delete operation")
                
        elif request.operation == "create_collection":
            # Create collection if it doesn't exist
            await service_db.create_collection(request.collection_name)
            result = {"message": f"Collection {request.collection_name} created"}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported operation: {request.operation}")
        
        return DatabaseResponse(
            success=True,
            data=result,
            message=f"MongoDB {request.operation} operation successful",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"MongoDB operation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"MongoDB operation failed: {str(e)}"
        )

@app.get("/api/mongodb/collections/{service_name}/{database_name}")
async def list_collections(service_name: str, database_name: str):
    """List all collections for a service database"""
    try:
        service_db = client[f"{service_name}_{database_name}"]
        collections = await service_db.list_collection_names()
        return {
            "success": True,
            "collections": collections,
            "message": f"Collections for {service_name}_{database_name}",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mongodb/databases/{service_name}")
async def list_databases(service_name: str):
    """List all databases for a service"""
    try:
        databases = await client.list_database_names()
        service_databases = [db for db in databases if db.startswith(f"{service_name}_")]
        return {
            "success": True,
            "databases": service_databases,
            "message": f"Databases for service {service_name}",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
