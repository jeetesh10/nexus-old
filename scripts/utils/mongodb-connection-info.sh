#!/bin/bash

# MongoDB UI Connection Details
# =============================
# Use this information to connect to MongoDB with UI tools

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📱 MongoDB UI Connection Information${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Get credentials from Kubernetes secret
MONGO_USER=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.root-username}' | base64 -d 2>/dev/null || echo "admin")
MONGO_PASS=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.root-password}' | base64 -d 2>/dev/null || echo "")
MONGO_DB=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.database}' | base64 -d 2>/dev/null || echo "nexus")

echo -e "${GREEN}🔧 MongoDB Connection Details:${NC}"
echo "   Host: localhost"
echo "   Port: 27017"
echo "   Username: $MONGO_USER"
echo "   Password: $MONGO_PASS"
echo "   Database: $MONGO_DB"
echo "   Auth Database: admin"
echo ""

echo -e "${GREEN}🔗 Connection String (for MongoDB Compass):${NC}"
echo "   mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/$MONGO_DB?authSource=admin"
echo ""

echo -e "${GREEN}📱 MongoDB Compass Setup:${NC}"
echo "   1. Download MongoDB Compass from: https://www.mongodb.com/products/compass"
echo "   2. Open Compass and paste the connection string above"
echo "   3. Or enter connection details manually:"
echo "      - Hostname: localhost"
echo "      - Port: 27017" 
echo "      - Authentication: Username/Password"
echo "      - Username: $MONGO_USER"
echo "      - Password: $MONGO_PASS"
echo "      - Authentication Database: admin"
echo "      - Default Database: $MONGO_DB"
echo ""

echo -e "${GREEN}🌐 Alternative: Mongo Express (Web UI):${NC}"
echo "   Run this Docker command to start a web UI:"
echo "   docker run -d --name mongo-express --network host \\"
echo "     -e ME_CONFIG_MONGODB_URL=\"mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/$MONGO_DB?authSource=admin\" \\"
echo "     -e ME_CONFIG_BASICAUTH_USERNAME=admin \\"
echo "     -e ME_CONFIG_BASICAUTH_PASSWORD=admin \\"
echo "     -p 8081:8081 \\"
echo "     mongo-express"
echo "   Then open: http://localhost:8081"
echo ""

echo -e "${GREEN}💻 Command Line Access:${NC}"
echo "   mongosh \"mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/$MONGO_DB?authSource=admin\""
echo ""

# Check if port forwarding is active
echo -e "${BLUE}🔌 Port Forwarding Status:${NC}"
if lsof -i :27017 &> /dev/null; then
    echo -e "${GREEN}   ✅ Port 27017 is active and ready for connections${NC}"
else
    echo -e "${YELLOW}   ⚠️  Port 27017 not accessible${NC}"
    echo "   Run this to start port forwarding:"
    echo "   kubectl port-forward -n mongodb svc/mongodb 27017:27017"
    echo ""
fi

# Check MongoDB pod status
echo -e "${BLUE}📊 MongoDB Pod Status:${NC}"
kubectl get pods -n mongodb -o wide
echo ""

echo -e "${YELLOW}🔍 Manual Testing Steps:${NC}"
echo "1. 📱 Connect using MongoDB Compass with the connection string above"
echo "2. 🗂️  Navigate to database: '$MONGO_DB'"
echo "3. 📝 Try creating a test collection manually:"
echo "   - Collection name: 'manual_test'"
echo "   - Insert a document: {\"test\": true, \"created\": new Date(), \"user\": \"manual\"}"
echo "4. 🔍 Verify the document appears in the collection"
echo "5. ✅ If successful, MongoDB is working correctly!"
echo ""

echo -e "${GREEN}📋 What to Verify:${NC}"
echo "   ✅ Can connect to MongoDB"
echo "   ✅ Can see database '$MONGO_DB'"
echo "   ✅ Can create collections"
echo "   ✅ Can insert documents"
echo "   ✅ Can query documents"
echo "   ✅ Authentication is working"
echo ""

# Try a simple test if possible
echo -e "${BLUE}🧪 Quick Connection Test:${NC}"
if kubectl exec -n mongodb mongodb-0 -- mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
    echo -e "${GREEN}   ✅ MongoDB is responding to ping${NC}"
    
    # Try to get server info
    SERVER_INFO=$(kubectl exec -n mongodb mongodb-0 -- mongosh --quiet --eval "JSON.stringify(db.serverStatus().version)" 2>/dev/null || echo "Unknown")
    if [[ "$SERVER_INFO" != "Unknown" ]]; then
        CLEAN_VERSION=$(echo "$SERVER_INFO" | tr -d '"')
        echo -e "${GREEN}   ✅ MongoDB Version: $CLEAN_VERSION${NC}"
    fi
else
    echo -e "${RED}   ❌ MongoDB is not responding${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Ready for manual testing with UI tools!${NC}"
echo -e "${YELLOW}   After testing, confirm that MongoDB is working correctly${NC}"
echo -e "${YELLOW}   and we'll proceed with committing the deployment.${NC}"
