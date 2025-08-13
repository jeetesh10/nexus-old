# Database Orchestrator Services Usage Examples

## Overview

The Nexus Platform provides **two separate database orchestrator services**:

1. **MongoDB Orchestrator Service** - Handles all MongoDB operations
2. **PostgreSQL Orchestrator Service** - Handles all PostgreSQL operations

## Architecture

```
Client App → MongoDB Orchestrator → MongoDB Database
Client App → PostgreSQL Orchestrator → PostgreSQL Database
```

## MongoDB Orchestrator Service

### Base URL
```
http://mongodb-orchestrator.local
```

### Health Check
```bash
curl http://mongodb-orchestrator.local/health
```

### Insert Document
```bash
curl -X POST http://mongodb-orchestrator.local/api/mongodb/operation \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "user-service",
    "database_name": "users",
    "collection_name": "profiles",
    "operation": "insert",
    "data": {
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2024-01-01T00:00:00Z"
    }
  }'
```

### Find Documents
```bash
curl -X POST http://mongodb-orchestrator.local/api/mongodb/operation \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "user-service",
    "database_name": "users",
    "collection_name": "profiles",
    "operation": "find",
    "query": {
      "email": "john@example.com"
    }
  }'
```

### Update Documents
```bash
curl -X POST http://mongodb-orchestrator.local/api/mongodb/operation \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "user-service",
    "database_name": "users",
    "collection_name": "profiles",
    "operation": "update",
    "query": {
      "email": "john@example.com"
    },
    "update": {
      "$set": {
        "last_login": "2024-01-02T00:00:00Z"
      }
    }
  }'
```

## PostgreSQL Orchestrator Service

### Base URL
```
http://postgresql-orchestrator.local
```

### Health Check
```bash
curl http://postgresql-orchestrator.local/health
```

### Create Table
```bash
curl -X POST http://postgresql-orchestrator.local/api/postgresql/operation \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "order-service",
    "database_name": "orders",
    "table_name": "orders",
    "operation": "create_table",
    "data": {
      "id": "SERIAL PRIMARY KEY",
      "user_id": "INTEGER NOT NULL",
      "product_id": "INTEGER NOT NULL",
      "quantity": "INTEGER NOT NULL",
      "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }
  }'
```

### Insert Record
```bash
curl -X POST http://postgresql-orchestrator.local/api/postgresql/operation \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "order-service",
    "database_name": "orders",
    "table_name": "orders",
    "operation": "insert",
    "columns": ["user_id", "product_id", "quantity"],
    "data": {
      "user_id": 123,
      "product_id": 456,
      "quantity": 2
    }
  }'
```

### Select Records
```bash
curl -X POST http://postgresql-orchestrator.local/api/postgresql/operation \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "order-service",
    "database_name": "orders",
    "table_name": "orders",
    "operation": "select",
    "query": "SELECT * FROM order-service_orders.orders WHERE user_id = $1",
    "params": [123]
  }'
```

## Service Isolation

Each service gets its own **isolated database/collection**:

### MongoDB
- Service: `user-service`
- Database: `user-service_users`
- Collection: `profiles`

### PostgreSQL
- Service: `order-service`
- Schema: `order-service_orders`
- Table: `orders`

## Benefits

1. **Service Isolation** - Each service has its own database space
2. **Independent Scaling** - Scale MongoDB and PostgreSQL services separately
3. **Fault Isolation** - If one service fails, the other continues working
4. **Future-Proof** - Easy to migrate to managed services later
5. **No Database Dependencies** - Clients don't need database drivers

## Error Handling

All operations return consistent response format:

```json
{
  "success": true,
  "data": {...},
  "message": "Operation successful",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Monitoring

- Health endpoints: `/health`
- API documentation: `/docs`
- Metrics: Prometheus endpoints (future)
