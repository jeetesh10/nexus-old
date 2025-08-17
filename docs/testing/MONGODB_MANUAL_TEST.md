# MongoDB Manual Test Instructions

## Connection Details
- **Host:** localhost
- **Port:** 27017
- **Username:** admin
- **Password:** urHh87Q9pETZkAMLAoAQoeKV3
- **Database:** nexus
- **Auth Database:** admin

## Connection String
```
mongodb://admin:urHh87Q9pETZkAMLAoAQoeKV3@localhost:27017/nexus?authSource=admin
```

## Testing with MongoDB Compass

1. **Download & Install MongoDB Compass**
   - Go to: https://www.mongodb.com/products/compass
   - Download for your operating system
   - Install and open Compass

2. **Connect to MongoDB**
   - Option A: Paste the connection string above into the connection field
   - Option B: Fill in connection details manually:
     - Hostname: `localhost`
     - Port: `27017`
     - Authentication: Username/Password
     - Username: `admin`
     - Password: `urHh87Q9pETZkAMLAoAQoeKV3`
     - Authentication Database: `admin`
     - Default Database: `nexus`

3. **Verify Connection**
   - Click "Connect"
   - You should see the MongoDB server information
   - Navigate to the `nexus` database

## Manual Test Cases

### Test Case 1: Create Collection
1. In Compass, navigate to database `nexus`
2. Click "Create Collection"
3. Name: `manual_test_collection`
4. Click "Create Collection"

### Test Case 2: Insert Document
1. Open the `manual_test_collection`
2. Click "Insert Document"
3. Paste this JSON:
```json
{
  "test_name": "Manual Connection Test",
  "created_by": "User",
  "timestamp": "2025-08-16T16:40:00Z",
  "platform": "nexus",
  "database": "mongodb",
  "version": "7.0.23",
  "status": "testing",
  "metadata": {
    "deployment_script": "platform-mongodb.sh",
    "test_type": "manual_verification",
    "success": true
  }
}
```
4. Click "Insert"

### Test Case 3: Query Document
1. In the collection view, you should see the inserted document
2. Try filtering with: `{"status": "testing"}`
3. Verify the document appears in results

### Test Case 4: Create Index
1. Go to "Indexes" tab in the collection
2. Click "Create Index"
3. Index: `{"test_name": 1}`
4. Click "Create Index"

### Test Case 5: Insert Multiple Documents
1. Insert these additional test documents:

**User Document:**
```json
{
  "type": "user",
  "username": "test_user_1",
  "email": "user1@nexus.local",
  "role": "admin",
  "created_at": "2025-08-16T16:40:00Z",
  "last_login": null,
  "active": true
}
```

**Service Document:**
```json
{
  "type": "service",
  "service_name": "mongodb",
  "status": "running",
  "port": 27017,
  "replicas": 1,
  "health_check": "passed",
  "deployed_at": "2025-08-16T16:25:00Z"
}
```

**Config Document:**
```json
{
  "type": "configuration",
  "component": "platform",
  "settings": {
    "auth_enabled": true,
    "ssl_enabled": false,
    "max_connections": 1000,
    "timeout": 30
  },
  "updated_at": "2025-08-16T16:40:00Z"
}
```

## Expected Results
After completing all test cases, you should have:
- ✅ Successfully connected to MongoDB
- ✅ Created collection `manual_test_collection`
- ✅ Inserted 4 documents total
- ✅ Successfully queried documents
- ✅ Created an index on `test_name` field
- ✅ All documents visible and properly formatted
- ✅ No authentication or connection errors

## Alternative Testing with Mongo Express

If you prefer a web interface:

1. **Start Mongo Express:**
```bash
docker run -d --name mongo-express --network host \
  -e ME_CONFIG_MONGODB_URL="mongodb://admin:urHh87Q9pETZkAMLAoAQoeKV3@localhost:27017/nexus?authSource=admin" \
  -e ME_CONFIG_BASICAUTH_USERNAME=admin \
  -e ME_CONFIG_BASICAUTH_PASSWORD=admin \
  -p 8081:8081 \
  mongo-express
```

2. **Access Web UI:**
   - Open: http://localhost:8081
   - Login: admin / admin
   - Navigate to `nexus` database
   - Perform the same test cases as above

## Verification Checklist
- [ ] Can connect to MongoDB without errors
- [ ] Can see `nexus` database
- [ ] Can create collections
- [ ] Can insert documents
- [ ] Can query and filter documents  
- [ ] Can create indexes
- [ ] All data persists between operations
- [ ] No authentication failures
- [ ] MongoDB version shows as 7.0.23

## Troubleshooting

**If connection fails:**
1. Verify port forwarding is active: `lsof -i :27017`
2. Check MongoDB pod status: `kubectl get pods -n mongodb`
3. Restart port forwarding: `kubectl port-forward -n mongodb svc/mongodb 27017:27017`

**If authentication fails:**
1. Double-check username/password from script output
2. Ensure authentication database is set to `admin`
3. Try connecting without specifying a default database first

## Ready to Commit
Once you've successfully completed the manual testing and verified that:
1. MongoDB is accessible via UI tools
2. You can create/read/update/delete data
3. Authentication is working properly
4. All test documents are visible and properly stored

Then we're ready to commit the MongoDB deployment and proceed to the next database (Neo4j/PostgreSQL)!
