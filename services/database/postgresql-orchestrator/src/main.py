from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncpg
import asyncio
import logging
from datetime import datetime
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PostgreSQL Orchestrator Service",
    description="Orchestrated PostgreSQL operations for microservices",
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

# PostgreSQL connection pool for admin operations
POSTGRES_ADMIN_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:password@postgresql-service:5432")
admin_pool = None
service_pools = {}  # Cache for service-specific pools

# Connection pool configuration
POOL_CONFIG = {
    "min_size": 2,
    "max_size": 10,
    "command_timeout": 60,
    "server_settings": {
        "application_name": "postgresql_orchestrator"
    }
}

async def get_admin_pool():
    """Get admin database connection pool for creating databases"""
    global admin_pool
    if admin_pool is None:
        admin_pool = await asyncpg.create_pool(
            POSTGRES_ADMIN_URL,
            **POOL_CONFIG
        )
    return admin_pool

async def get_service_pool(service_name: str, database_name: str):
    """Get service-specific database connection pool with caching"""
    global service_pools
    
    # Create unique key for this service database
    pool_key = f"{service_name}_{database_name}"
    
    if pool_key not in service_pools:
        # Create service-specific database URL
        service_db_name = f"{service_name}_{database_name}".replace("-", "_")
        service_url = f"postgresql://postgres:password@postgresql-service:5432/{service_db_name}"
        
        # Create a new pool for this service's database
        service_pools[pool_key] = await asyncpg.create_pool(
            service_url,
            **POOL_CONFIG
        )
    
    return service_pools[pool_key]

async def close_all_pools():
    """Close all connection pools"""
    global admin_pool, service_pools
    
    if admin_pool:
        await admin_pool.close()
        admin_pool = None
    
    for pool in service_pools.values():
        await pool.close()
    service_pools.clear()

# Pydantic models
class DatabaseRequest(BaseModel):
    service_name: str
    database_name: str
    table_name: str
    operation: str
    data: Optional[Dict[str, Any]] = None
    query: Optional[str] = None
    params: Optional[List[Any]] = None
    columns: Optional[List[str]] = None

class DatabaseCreateRequest(BaseModel):
    service_name: str
    database_name: str
    description: Optional[str] = None

class DatabaseResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: str
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    postgresql_connected: bool
    timestamp: datetime

class PoolStatusResponse(BaseModel):
    admin_pool_status: str
    service_pools_count: int
    total_connections: int
    timestamp: datetime

@app.on_event("startup")
async def startup():
    """Initialize admin database connection pool"""
    global admin_pool
    try:
        admin_pool = await asyncpg.create_pool(
            POSTGRES_ADMIN_URL,
            **POOL_CONFIG
        )
        logger.info("PostgreSQL admin connection pool created")
        logger.info(f"Pool configuration: {POOL_CONFIG}")
    except Exception as e:
        logger.error(f"Failed to create PostgreSQL admin connection pool: {e}")

@app.on_event("shutdown")
async def shutdown():
    """Close all database connection pools"""
    await close_all_pools()
    logger.info("All PostgreSQL connection pools closed")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        admin_pool = await get_admin_pool()
        async with admin_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        postgresql_connected = True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        postgresql_connected = False
    
    return HealthResponse(
        status="healthy" if postgresql_connected else "unhealthy",
        postgresql_connected=postgresql_connected,
        timestamp=datetime.utcnow()
    )

@app.get("/api/postgresql/pool-status", response_model=PoolStatusResponse)
async def get_pool_status():
    """Get connection pool status"""
    try:
        admin_status = "connected" if admin_pool else "disconnected"
        service_pools_count = len(service_pools)
        
        # Calculate total connections
        total_connections = 0
        if admin_pool:
            total_connections += admin_pool.get_size()
        
        for pool in service_pools.values():
            total_connections += pool.get_size()
        
        return PoolStatusResponse(
            admin_pool_status=admin_status,
            service_pools_count=service_pools_count,
            total_connections=total_connections,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Failed to get pool status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/postgresql/database", response_model=DatabaseResponse)
async def create_database(request: DatabaseCreateRequest):
    """Create a new database for a service"""
    try:
        admin_pool = await get_admin_pool()
        async with admin_pool.acquire() as conn:
            # Create service-specific database name
            database_name = f"{request.service_name}_{request.database_name}".replace("-", "_")
            
            # Check if database already exists
            existing_dbs = await conn.fetch(
                "SELECT datname FROM pg_database WHERE datname = $1",
                database_name
            )
            
            if existing_dbs:
                return DatabaseResponse(
                    success=True,
                    data={"database_name": database_name, "message": "Database already exists"},
                    message="Database already exists",
                    timestamp=datetime.utcnow()
                )
            
            # Create the database
            await conn.execute(f'CREATE DATABASE "{database_name}"')
            
            # Connect to the new database to create metadata table
            service_pool = await get_service_pool(request.service_name, request.database_name)
            async with service_pool.acquire() as service_conn:
                # Create metadata table
                metadata_table = '''CREATE TABLE IF NOT EXISTS database_metadata (
                    id SERIAL PRIMARY KEY,
                    service_name VARCHAR(255) NOT NULL,
                    database_name VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )'''
                
                await service_conn.execute(metadata_table)
                
                # Insert metadata
                await service_conn.execute(
                    'INSERT INTO database_metadata (service_name, database_name, description) VALUES ($1, $2, $3)',
                    request.service_name, request.database_name, request.description
                )
            
            await service_pool.close()
            
            return DatabaseResponse(
                success=True,
                data={
                    "database_name": database_name,
                    "service_name": request.service_name,
                    "database_name_original": request.database_name,
                    "description": request.description
                },
                message="Database created successfully",
                timestamp=datetime.utcnow()
            )
            
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        raise HTTPException(status_code=500, detail=f"PostgreSQL operation failed: {str(e)}")

@app.get("/api/postgresql/databases/{service_name}")
async def list_databases(service_name: str):
    """List all databases for a service"""
    try:
        admin_pool = await get_admin_pool()
        async with admin_pool.acquire() as conn:
            # Get all databases for this service
            query = """
                SELECT datname 
                FROM pg_database 
                WHERE datname LIKE $1
                ORDER BY datname
            """
            result = await conn.fetch(query, f"{service_name.replace('-', '_')}_%")
            
            databases = []
            for row in result:
                database_name = row['datname']
                # Extract database name from full database name
                db_name = database_name.replace(f"{service_name.replace('-', '_')}_", "", 1)
                
                # Try to get metadata from the service database
                try:
                    service_pool = await get_service_pool(service_name, db_name)
                    async with service_pool.acquire() as service_conn:
                        metadata = await service_conn.fetchrow(
                            'SELECT * FROM database_metadata LIMIT 1'
                        )
                        if metadata:
                            databases.append({
                                "database_name": database_name,
                                "database_name_original": db_name,
                                "description": metadata.get('description'),
                                "created_at": metadata.get('created_at').isoformat() if metadata.get('created_at') else None
                            })
                        else:
                            databases.append({
                                "database_name": database_name,
                                "database_name_original": db_name,
                                "description": None,
                                "created_at": None
                            })
                    await service_pool.close()
                except:
                    # If metadata table doesn't exist, just return basic info
                    databases.append({
                        "database_name": database_name,
                        "database_name_original": db_name,
                        "description": None,
                        "created_at": None
                    })
            
            return DatabaseResponse(
                success=True,
                data={"databases": databases},
                message=f"Databases for service {service_name}",
                timestamp=datetime.utcnow()
            )
            
    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        raise HTTPException(status_code=500, detail=f"PostgreSQL operation failed: {str(e)}")

@app.post("/api/postgresql/operation", response_model=DatabaseResponse)
async def postgresql_operation(request: DatabaseRequest):
    """Generic PostgreSQL operation endpoint"""
    try:
        # Get service-specific database pool
        pool = await get_service_pool(request.service_name, request.database_name)
        async with pool.acquire() as conn:
            
            result = None
            
            if request.operation == "insert":
                if request.data and request.columns:
                    # Build INSERT query
                    columns = ", ".join(request.columns)
                    placeholders = ", ".join([f"${i+1}" for i in range(len(request.columns))])
                    values = [request.data.get(col) for col in request.columns]
                    
                    query = f"INSERT INTO {request.table_name} ({columns}) VALUES ({placeholders}) RETURNING *"
                    result = await conn.fetchrow(query, *values)
                    result = dict(result) if result else None
                else:
                    raise HTTPException(status_code=400, detail="Data and columns required for insert operation")
                    
            elif request.operation == "select":
                if request.query:
                    result = await conn.fetch(request.query, *(request.params or []))
                    result = [dict(row) for row in result]
                else:
                    # Select all from table
                    query = f"SELECT * FROM {request.table_name}"
                    result = await conn.fetch(query)
                    result = [dict(row) for row in result]
                    
            elif request.operation == "update":
                if request.query and request.data:
                    # Build UPDATE query
                    set_clause = ", ".join([f"{k} = ${i+1}" for i, k in enumerate(request.data.keys())])
                    values = list(request.data.values())
                    
                    query = f"UPDATE {request.table_name} SET {set_clause} WHERE {request.query}"
                    result = await conn.execute(query, *values)
                    result = {"affected_rows": result}
                else:
                    raise HTTPException(status_code=400, detail="Query and data required for update operation")
                    
            elif request.operation == "delete":
                if request.query:
                    query = f"DELETE FROM {request.table_name} WHERE {request.query}"
                    result = await conn.execute(query, *(request.params or []))
                    result = {"affected_rows": result}
                else:
                    raise HTTPException(status_code=400, detail="Query required for delete operation")
                    
            elif request.operation == "create_table":
                if request.data:
                    # Create table with provided schema
                    columns_def = []
                    for col_name, col_type in request.data.items():
                        columns_def.append(f"{col_name} {col_type}")
                    
                    columns_sql = ", ".join(columns_def)
                    query = f"CREATE TABLE IF NOT EXISTS {request.table_name} ({columns_sql})"
                    await conn.execute(query)
                    result = {"message": f"Table {request.table_name} created successfully"}
                else:
                    raise HTTPException(status_code=400, detail="Table schema required for create_table operation")
                    
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported operation: {request.operation}")
            
            return DatabaseResponse(
                success=True,
                data=result,
                message=f"PostgreSQL {request.operation} operation successful",
                timestamp=datetime.utcnow()
            )
            
    except Exception as e:
        logger.error(f"PostgreSQL operation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PostgreSQL operation failed: {str(e)}"
        )

@app.get("/api/postgresql/tables/{service_name}/{database_name}")
async def list_tables(service_name: str, database_name: str):
    """List all tables for a service database"""
    try:
        pool = await get_service_pool(service_name, database_name)
        async with pool.acquire() as conn:
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """
            result = await conn.fetch(query)
            tables = [row['table_name'] for row in result]
            
            return {
                "success": True,
                "tables": tables,
                "message": f"Tables for {service_name}_{database_name}",
                "timestamp": datetime.utcnow()
            }
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
