# Database Orchestrator Service Integration Guide

## Overview

This guide explains how other services in the Nexus Platform should integrate with the Database Orchestrator Services.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Your Service  │    │   Your Service  │
│   (MongoDB)     │    │   (PostgreSQL)  │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│   MongoDB       │    │   PostgreSQL    │
│   Orchestrator  │    │   Orchestrator  │
│   Service       │    │   Service       │
└─────────────────┘    └─────────────────┘
```

## Service URLs

- **MongoDB Orchestrator**: `http://mongodb-orchestrator-service:8000`
- **PostgreSQL Orchestrator**: `http://postgresql-orchestrator-service:8000`

## Integration Patterns

### 1. HTTP Client Integration

```python
import httpx
import asyncio
from typing import Dict, Any

class DatabaseClient:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.mongodb_url = "http://mongodb-orchestrator-service:8000"
        self.postgresql_url = "http://postgresql-orchestrator-service:8000"
    
    async def mongodb_operation(self, database: str, collection: str, operation: str, **kwargs):
        """Execute MongoDB operation"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.mongodb_url}/api/mongodb/operation",
                json={
                    "service_name": self.service_name,
                    "database_name": database,
                    "collection_name": collection,
                    "operation": operation,
                    **kwargs
                }
            )
            return response.json()
    
    async def postgresql_operation(self, database: str, table: str, operation: str, **kwargs):
        """Execute PostgreSQL operation"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.postgresql_url}/api/postgresql/operation",
                json={
                    "service_name": self.service_name,
                    "database_name": database,
                    "table_name": table,
                    "operation": operation,
                    **kwargs
                }
            )
            return response.json()

# Usage Example
async def main():
    db_client = DatabaseClient("user-service")
    
    # MongoDB operations
    await db_client.mongodb_operation(
        database="users",
        collection="profiles",
        operation="insert",
        data={"name": "John", "email": "john@example.com"}
    )
    
    # PostgreSQL operations
    await db_client.postgresql_operation(
        database="orders",
        table="orders",
        operation="insert",
        columns=["user_id", "product_id"],
        data={"user_id": 123, "product_id": 456}
    )
```

### 2. FastAPI Service Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str

class UserService:
    def __init__(self):
        self.service_name = "user-service"
        self.mongodb_url = "http://mongodb-orchestrator-service:8000"
    
    async def create_user(self, user_data: UserCreate):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.mongodb_url}/api/mongodb/operation",
                json={
                    "service_name": self.service_name,
                    "database_name": "users",
                    "collection_name": "profiles",
                    "operation": "insert",
                    "data": user_data.dict()
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Database operation failed")
            
            return response.json()

user_service = UserService()

@app.post("/users")
async def create_user(user: UserCreate):
    return await user_service.create_user(user)
```

### 3. Node.js Service Integration

```javascript
const axios = require('axios');

class DatabaseClient {
    constructor(serviceName) {
        this.serviceName = serviceName;
        this.mongodbUrl = 'http://mongodb-orchestrator-service:8000';
        this.postgresqlUrl = 'http://postgresql-orchestrator-service:8000';
    }

    async mongodbOperation(database, collection, operation, data = {}) {
        try {
            const response = await axios.post(`${this.mongodbUrl}/api/mongodb/operation`, {
                service_name: this.serviceName,
                database_name: database,
                collection_name: collection,
                operation: operation,
                ...data
            });
            return response.data;
        } catch (error) {
            throw new Error(`MongoDB operation failed: ${error.message}`);
        }
    }

    async postgresqlOperation(database, table, operation, data = {}) {
        try {
            const response = await axios.post(`${this.postgresqlUrl}/api/postgresql/operation`, {
                service_name: this.serviceName,
                database_name: database,
                table_name: table,
                operation: operation,
                ...data
            });
            return response.data;
        } catch (error) {
            throw new Error(`PostgreSQL operation failed: ${error.message}`);
        }
    }
}

// Usage Example
const dbClient = new DatabaseClient('order-service');

async function createOrder(orderData) {
    return await dbClient.postgresqlOperation(
        'orders',
        'orders',
        'insert',
        {
            columns: ['user_id', 'product_id', 'quantity'],
            data: orderData
        }
    );
}
```

## Service Naming Convention

### Database Names
- **MongoDB**: `{service-name}_{database-name}`
- **PostgreSQL**: `{service-name}_{database-name}` (schema)

### Examples
- Service: `user-service`, Database: `users` → MongoDB: `user-service_users`
- Service: `order-service`, Database: `orders` → PostgreSQL Schema: `order-service_orders`

## Common Operations

### MongoDB Operations

```python
# Insert document
await db_client.mongodb_operation(
    database="users",
    collection="profiles",
    operation="insert",
    data={"name": "John", "email": "john@example.com"}
)

# Find documents
result = await db_client.mongodb_operation(
    database="users",
    collection="profiles",
    operation="find",
    query={"email": "john@example.com"}
)

# Update documents
await db_client.mongodb_operation(
    database="users",
    collection="profiles",
    operation="update",
    query={"email": "john@example.com"},
    update={"$set": {"last_login": "2024-01-01T00:00:00Z"}}
)

# Delete documents
await db_client.mongodb_operation(
    database="users",
    collection="profiles",
    operation="delete",
    query={"email": "john@example.com"}
)
```

### PostgreSQL Operations

```python
# Create table
await db_client.postgresql_operation(
    database="orders",
    table="orders",
    operation="create_table",
    data={
        "id": "SERIAL PRIMARY KEY",
        "user_id": "INTEGER NOT NULL",
        "product_id": "INTEGER NOT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }
)

# Insert record
await db_client.postgresql_operation(
    database="orders",
    table="orders",
    operation="insert",
    columns=["user_id", "product_id"],
    data={"user_id": 123, "product_id": 456}
)

# Select records
result = await db_client.postgresql_operation(
    database="orders",
    table="orders",
    operation="select",
    query="SELECT * FROM order-service_orders.orders WHERE user_id = $1",
    params=[123]
)

# Update records
await db_client.postgresql_operation(
    database="orders",
    table="orders",
    operation="update",
    query="user_id = $1",
    data={"status": "completed"},
    params=[123]
)
```

## Error Handling

```python
async def safe_database_operation(operation_func, *args, **kwargs):
    try:
        result = await operation_func(*args, **kwargs)
        if result.get('success'):
            return result['data']
        else:
            raise Exception(result.get('message', 'Database operation failed'))
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Usage
user_data = await safe_database_operation(
    db_client.mongodb_operation,
    database="users",
    collection="profiles",
    operation="insert",
    data={"name": "John", "email": "john@example.com"}
)
```

## Health Checks

```python
async def check_database_health():
    async with httpx.AsyncClient() as client:
        # Check MongoDB
        mongodb_health = await client.get("http://mongodb-orchestrator-service:8000/health")
        
        # Check PostgreSQL
        postgresql_health = await client.get("http://postgresql-orchestrator-service:8000/health")
        
        return {
            "mongodb": mongodb_health.json(),
            "postgresql": postgresql_health.json()
        }
```

## Best Practices

1. **Service Isolation**: Always use your service name as prefix for databases
2. **Error Handling**: Implement proper error handling for all database operations
3. **Connection Pooling**: Use HTTP client connection pooling for better performance
4. **Health Checks**: Implement health checks to monitor database connectivity
5. **Logging**: Log all database operations for debugging and monitoring
6. **Retry Logic**: Implement retry logic for transient failures
7. **Validation**: Validate data before sending to database orchestrators

## Migration from Direct Database Access

If you're migrating from direct database access:

1. **Replace database drivers** with HTTP client calls
2. **Update connection strings** to use orchestrator service URLs
3. **Modify queries** to use orchestrator API format
4. **Test thoroughly** to ensure data consistency
5. **Monitor performance** and adjust as needed

## Monitoring and Observability

```python
import time
import logging

async def monitored_database_operation(operation_func, *args, **kwargs):
    start_time = time.time()
    try:
        result = await operation_func(*args, **kwargs)
        duration = time.time() - start_time
        
        logging.info(f"Database operation completed in {duration:.2f}s")
        return result
    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Database operation failed after {duration:.2f}s: {e}")
        raise
```
