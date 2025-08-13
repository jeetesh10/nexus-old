# Database Access Quick Reference

## 🗄️ Direct Database Access (for UI Tools)

### MongoDB
- **Host**: `localhost`
- **Port**: `27017`
- **Username**: `admin`
- **Password**: `adminpass123`
- **Connection String**: `mongodb://admin:adminpass123@localhost:27017`

### PostgreSQL
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `postgres`
- **Username**: `postgres`
- **Password**: `password`
- **Connection String**: `postgresql://postgres:password@localhost:5432`

## 🔧 UI Tools Configuration

### MongoDB Compass / Studio 3T
```
Connection String: mongodb://admin:adminpass123@localhost:27017
```

### pgAdmin / DBeaver
```
Host: localhost
Port: 5432
Database: postgres
Username: postgres
Password: password
```

## 🚀 Orchestrator Service Access

### MongoDB Orchestrator
- **URL**: `http://localhost:8001`
- **Health**: `http://localhost:8001/health`
- **Docs**: `http://localhost:8001/docs`

### PostgreSQL Orchestrator
- **URL**: `http://localhost:8002`
- **Health**: `http://localhost:8002/health`
- **Docs**: `http://localhost:8002/docs`

## 📋 Quick Test Commands

### Test MongoDB Connection
```bash
# Test direct connection
mongosh mongodb://admin:adminpass123@localhost:27017

# Test orchestrator health
curl http://localhost:8001/health
```

### Test PostgreSQL Connection
```bash
# Test direct connection
psql postgresql://postgres:password@localhost:5432/postgres

# Test orchestrator health
curl http://localhost:8002/health
```

## 🎯 Service Integration URLs

### For Other Services (Internal)
- **MongoDB Orchestrator**: `http://mongodb-orchestrator-service:8000`
- **PostgreSQL Orchestrator**: `http://postgresql-orchestrator-service:8000`

### For External Access
- **MongoDB Orchestrator**: `http://mongodb-orchestrator.local`
- **PostgreSQL Orchestrator**: `http://postgresql-orchestrator.local`

## 📊 Database Structure

### MongoDB Collections
- Service databases: `{service-name}_{database-name}`
- Example: `user-service_users`, `order-service_orders`

### PostgreSQL Schemas
- Service schemas: `{service-name}_{database-name}`
- Example: `user-service_users`, `order-service_orders`

## 🔍 Monitoring

### Check Service Status
```bash
# Check all database-related pods
kubectl get pods -n default | grep -E "(mongodb|postgresql)"

# Check service logs
kubectl logs deployment/mongodb-orchestrator -n default
kubectl logs deployment/postgresql-orchestrator -n default
```

### Port Forward Status
```bash
# Check if port forwards are active
lsof -i :27017  # MongoDB
lsof -i :5432   # PostgreSQL
lsof -i :8001   # MongoDB Orchestrator
lsof -i :8002   # PostgreSQL Orchestrator
```
