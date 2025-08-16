# MongoDB Manual Testing Guide - Secure Implementation

## Overview
This guide covers manual testing of MongoDB deployment with secure secret management.

## Security Features ✅

### ✅ No Environment Variables for Secrets
- All sensitive data stored in Kubernetes secrets
- MongoDB deployment uses `secretKeyRef` for credential injection
- Mongo Express uses `secretKeyRef` for both MongoDB connection and UI authentication

### ✅ Proper Secret Management
- Secure password generation using `openssl`
- Credentials stored in `mongodb-credentials` secret
- Separate UI credentials for Mongo Express

### ✅ StatefulSet with Persistent Storage
- Uses StatefulSet instead of Deployment for data persistence
- PersistentVolumeClaim for `/data/db`
- Proper service discovery

### ✅ Network Security
- Linkerd injection disabled for database services
- ClusterIP services for internal communication
- Port forwarding for development access

## Quick Deployment Test

### 1. Deploy MongoDB
```bash
# Deploy with secure secret management
./scripts/deploy/platform-mongodb.sh --deploy-mongodb

# This will:
# - Create namespace with Linkerd exclusion
# - Generate secure credentials and store in Kubernetes secrets
# - Deploy MongoDB StatefulSet with persistent storage
# - Deploy Mongo Express UI with secret-based authentication
# - Set up port forwarding for both services
```

### 2. Verify Deployment
```bash
# Check health
./scripts/deploy/platform-mongodb.sh --check-health

# Test connection and create sample data
./scripts/deploy/platform-mongodb.sh --test-connection
```

### 3. Access Credentials Securely
```bash
# MongoDB credentials
MONGO_USER=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.root-username}' | base64 -d)
MONGO_PASS=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.root-password}' | base64 -d)

# Mongo Express UI credentials
UI_USER=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.ui-username}' | base64 -d)
UI_PASS=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.ui-password}' | base64 -d)

echo "MongoDB: $MONGO_USER / $MONGO_PASS"
echo "UI: $UI_USER / $UI_PASS"
```

### 4. Access Services
- **MongoDB**: `mongodb://localhost:27017` (use credentials from secret)
- **Mongo Express UI**: `http://localhost:8081` (use UI credentials from secret)

### 5. Manual Connection Test
```bash
# Using MongoDB shell (if installed locally)
MONGO_PASS=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.root-password}' | base64 -d)
mongosh "mongodb://admin:$MONGO_PASS@localhost:27017/nexus?authSource=admin"

# Test commands:
show dbs
use nexus
show collections
db.test_collection.find().pretty()
```

## Manual Testing with Mongo Express UI

### 1. Access Web Interface
1. Get UI credentials:
```bash
UI_USER=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.ui-username}' | base64 -d)
UI_PASS=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.ui-password}' | base64 -d)
echo "Login: $UI_USER / $UI_PASS"
```

2. Open browser: http://localhost:8081
3. Login with the credentials above

### 2. Verify Test Data
1. Navigate to `nexus` database
2. Check `test_collection` for automatically created sample data
3. You should see documents like:
```json
{
  "_id": "...",
  "name": "MongoDB Connection Test",
  "timestamp": "2025-08-16T17:46:31.846Z",
  "type": "connectivity_test",
  "status": "successful",
  "metadata": {
    "script": "platform-mongodb.sh",
    "version": "1.0.0",
    "deployment_date": "2025-08-16T17:46:31.846Z"
  }
}
```

### 3. Manual Test Cases

#### Test Case 1: Create New Collection
1. In Mongo Express, go to `nexus` database
2. Create new collection: `manual_test`
3. Insert test document:
```json
{
  "test_name": "Secure Implementation Test",
  "created_by": "Manual Testing",
  "timestamp": "2025-08-16T17:50:00Z",
  "security_features": {
    "secrets_in_k8s": true,
    "no_env_vars": true,
    "statefulset": true,
    "persistent_storage": true
  },
  "status": "success"
}
```

#### Test Case 2: Verify Persistence
1. Restart MongoDB pod:
```bash
kubectl delete pod mongodb-0 -n mongodb
kubectl wait --for=condition=ready pod/mongodb-0 -n mongodb
```
2. Refresh Mongo Express UI
3. Verify all data is still there (persistence test)

#### Test Case 3: Test User Management
1. In MongoDB shell or Mongo Express:
```javascript
use admin
db.getUsers()  // Should show admin user created via secret
```

## Testing with MongoDB Compass

### 1. Get Connection String Securely
```bash
MONGO_USER=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.root-username}' | base64 -d)
MONGO_PASS=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.root-password}' | base64 -d)
echo "mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/nexus?authSource=admin"
```

### 2. Connect with Compass
1. Download MongoDB Compass
2. Use the connection string above
3. Verify you can browse the `nexus` database
4. Check that test data is visible

## Security Verification Checklist

- [ ] ✅ No hardcoded passwords in deployment files
- [ ] ✅ All credentials stored in Kubernetes secrets
- [ ] ✅ MongoDB uses `secretKeyRef` instead of `env` for credentials
- [ ] ✅ Mongo Express uses `secretKeyRef` for both MongoDB and UI auth
- [ ] ✅ StatefulSet provides data persistence
- [ ] ✅ Linkerd injection disabled for database pods
- [ ] ✅ Generated passwords are strong and unique
- [ ] ✅ UI has separate authentication from MongoDB

## Test Results Summary

```
✅ MongoDB pod: Running and Ready
✅ Mongo Express pod: Running and Ready  
✅ Port forwarding: Active (27017, 8081)
✅ Secret management: All credentials in K8s secrets
✅ Authentication: Working with secret-based credentials
✅ Data persistence: StatefulSet with PVC working
✅ UI Access: Mongo Express accessible with secure login
✅ No environment variables: All secrets via secretKeyRef
✅ Network security: Linkerd exclusion applied
```

## Sample Data Created Automatically
```json
{
  "name": "MongoDB Connection Test",
  "timestamp": "2025-08-16T17:46:31.846Z",
  "type": "connectivity_test",
  "status": "successful",
  "metadata": {
    "script": "platform-mongodb.sh",
    "version": "1.0.0",
    "deployment_date": "2025-08-16T17:46:31.846Z"
  }
}
```

## Cleanup
```bash
./scripts/deploy/platform-mongodb.sh --cleanup
```

## Ready for Next Database

This implementation demonstrates:
1. **Security First**: No sensitive data in environment variables
2. **Modular Design**: Clear separation of concerns
3. **Production Ready**: StatefulSet with persistent storage
4. **QA Friendly**: UI access for testing and verification
5. **Maintainable**: Secret management ready for Vault integration

Once manual testing is completed successfully, we can:
1. Commit the MongoDB secure implementation
2. Create a separate branch for Neo4j deployment
3. Apply the same security patterns to PostgreSQL and Neo4j

## Next Steps
- [ ] Integrate with Vault/External Secrets when ready
- [ ] Deploy PostgreSQL with same security approach
- [ ] Deploy Neo4j with same security approach
- [ ] Add monitoring and alerting
- [ ] Implement backup/restore procedures
