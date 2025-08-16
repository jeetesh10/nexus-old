#!/bin/bash

# MongoDB Connection Test Script
# =============================
# This script tests MongoDB connectivity and creates test data
# that you can verify through MongoDB UI tools.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script info
SCRIPT_VERSION="1.0.0"
echo -e "${BLUE}🚀 MongoDB Connection Test Script${NC}"
echo -e "${BLUE}=================================${NC}"
echo "[INFO] Script version: $SCRIPT_VERSION"
echo "[INFO] Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Function to get MongoDB credentials
get_mongodb_credentials() {
    echo -e "${BLUE}🔑 Getting MongoDB credentials...${NC}"
    
    MONGO_USER=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.root-username}' | base64 -d 2>/dev/null || echo "")
    MONGO_PASS=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.root-password}' | base64 -d 2>/dev/null || echo "")
    MONGO_DB=$(kubectl get secret mongodb-credentials -n mongodb -o jsonpath='{.data.database}' | base64 -d 2>/dev/null || echo "")
    
    if [[ -z "$MONGO_USER" || -z "$MONGO_PASS" || -z "$MONGO_DB" ]]; then
        echo -e "${RED}❌ Failed to get MongoDB credentials${NC}"
        echo "Make sure MongoDB is deployed and secrets exist"
        return 1
    fi
    
    echo -e "${GREEN}✅ Credentials retrieved successfully${NC}"
    return 0
}

# Function to check port forwarding
check_port_forward() {
    echo -e "${BLUE}🔌 Checking MongoDB port forwarding...${NC}"
    
    if lsof -i :27017 &> /dev/null; then
        echo -e "${GREEN}✅ Port 27017 is active${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Port 27017 not accessible${NC}"
        echo "Starting port forwarding..."
        
        # Kill any existing port forwards
        pkill -f "kubectl port-forward.*mongodb" || true
        sleep 2
        
        # Start new port forward in background
        kubectl port-forward -n mongodb svc/mongodb 27017:27017 &> /dev/null &
        PORT_FORWARD_PID=$!
        
        # Wait for port forward to be ready
        for i in {1..10}; do
            if lsof -i :27017 &> /dev/null; then
                echo -e "${GREEN}✅ Port forwarding started successfully${NC}"
                return 0
            fi
            sleep 1
        done
        
        echo -e "${RED}❌ Failed to start port forwarding${NC}"
        return 1
    fi
}

# Function to test basic connectivity
test_connectivity() {
    echo -e "${BLUE}🔍 Testing MongoDB connectivity...${NC}"
    
    # Test using mongosh if available, otherwise kubectl exec
    if command -v mongosh &> /dev/null; then
        echo "[DEBUG] Using local mongosh client"
        CONNECTION_STRING="mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/$MONGO_DB?authSource=admin"
        
        if mongosh "$CONNECTION_STRING" --eval "db.adminCommand('ping')" &> /dev/null; then
            echo -e "${GREEN}✅ MongoDB connection successful (local mongosh)${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Local mongosh failed, trying kubectl exec...${NC}"
        fi
    fi
    
    # Fallback to kubectl exec
    echo "[DEBUG] Using kubectl exec to test connection"
    if kubectl exec -n mongodb mongodb-0 -- mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
        echo -e "${GREEN}✅ MongoDB connection successful (kubectl exec)${NC}"
        return 0
    else
        echo -e "${RED}❌ MongoDB connection failed${NC}"
        return 1
    fi
}

# Function to create test data
create_test_data() {
    echo -e "${BLUE}📝 Creating test data in MongoDB...${NC}"
    
    # Create temporary JavaScript file for mongosh
    local temp_script="/tmp/mongodb_test_script.js"
    cat > "$temp_script" << 'EOF'
// Switch to the target database
use('nexus');

// Create test collection and insert sample documents
db.test_collection.insertMany([
    {
        name: "Test User 1",
        email: "user1@nexus.local",
        role: "admin",
        created_at: new Date(),
        metadata: {
            test_run: true,
            version: "1.0",
            platform: "nexus",
            script_version: "1.0.0"
        }
    },
    {
        name: "Test User 2", 
        email: "user2@nexus.local",
        role: "user",
        created_at: new Date(),
        metadata: {
            test_run: true,
            version: "1.0", 
            platform: "nexus",
            script_version: "1.0.0"
        }
    },
    {
        name: "Test Service",
        type: "microservice",
        status: "running",
        created_at: new Date(),
        config: {
            port: 8080,
            replicas: 3,
            database: "mongodb"
        }
    },
    {
        name: "Keycloak Integration",
        type: "auth_service",
        status: "configured",
        created_at: new Date(),
        config: {
            realm: "nexus",
            admin_console: "http://localhost:8080",
            database: "postgresql"
        }
    },
    {
        name: "Platform Metrics",
        type: "monitoring",
        status: "active",
        created_at: new Date(),
        metrics: {
            users_count: 2,
            services_count: 3,
            databases_deployed: ["mongodb", "postgresql"],
            last_deployment: new Date()
        }
    }
]);

// Create some indexes for better performance
db.test_collection.createIndex({ "email": 1 }, { unique: true });
db.test_collection.createIndex({ "type": 1 });
db.test_collection.createIndex({ "created_at": 1 });

// Create a user management collection
db.user_management.insertMany([
    {
        user_id: "usr_001",
        username: "admin",
        role: "platform_admin",
        permissions: ["read", "write", "delete", "manage"],
        last_login: new Date(),
        status: "active"
    },
    {
        user_id: "usr_002", 
        username: "developer",
        role: "developer",
        permissions: ["read", "write"],
        last_login: new Date(),
        status: "active"
    }
]);

// Create application configuration collection
db.app_config.insertOne({
    app_name: "nexus-platform",
    version: "1.0.0",
    deployment_date: new Date(),
    components: {
        auth: {
            service: "keycloak",
            version: "26.0.7",
            status: "running"
        },
        database: {
            service: "mongodb", 
            version: "7.0.23",
            status: "running"
        },
        monitoring: {
            service: "prometheus",
            status: "planned"
        }
    },
    configuration: {
        max_users: 1000,
        session_timeout: 3600,
        debug_mode: false
    }
});

// Print results
print("=== Test Data Creation Results ===");
print("Test Collection Documents:", db.test_collection.countDocuments({}));
print("User Management Documents:", db.user_management.countDocuments({}));
print("App Config Documents:", db.app_config.countDocuments({}));
print("Total Collections:", db.getCollectionNames().length);

print("\n=== Sample Document ===");
printjson(db.test_collection.findOne());
EOF

    # Copy script to container and execute
    if kubectl cp "$temp_script" mongodb/mongodb-0:/tmp/test_script.js && \
       kubectl exec -n mongodb mongodb-0 -- mongosh "mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/$MONGO_DB?authSource=admin" --quiet /tmp/test_script.js; then
        echo -e "${GREEN}✅ Test data created successfully${NC}"
        rm -f "$temp_script"
        return 0
    else
        echo -e "${RED}❌ Failed to create test data${NC}"
        rm -f "$temp_script"
        return 1
    fi
}

# Function to print connection information
print_connection_info() {
    echo ""
    echo -e "${BLUE}📱 MongoDB UI Tool Connection Information${NC}"
    echo -e "${BLUE}=========================================${NC}"
    
    echo ""
    echo -e "${GREEN}🔧 Connection Details:${NC}"
    echo "   Host: localhost"
    echo "   Port: 27017"
    echo "   Username: $MONGO_USER"
    echo "   Password: $MONGO_PASS"
    echo "   Database: $MONGO_DB"
    echo "   Auth Database: admin"
    
    echo ""
    echo -e "${GREEN}🔗 Connection String:${NC}"
    echo "   mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/$MONGO_DB?authSource=admin"
    
    echo ""
    echo -e "${GREEN}📱 For MongoDB Compass:${NC}"
    echo "   1. Download from: https://www.mongodb.com/products/compass"
    echo "   2. Use connection string above, or enter details manually"
    echo "   3. Look for database: '$MONGO_DB'"
    echo "   4. Verify collections: test_collection, user_management, app_config"
    
    echo ""
    echo -e "${GREEN}🌐 For Mongo Express (web UI):${NC}"
    echo "   docker run -it --rm --network host \\"
    echo "     -e ME_CONFIG_MONGODB_URL=\"mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/$MONGO_DB?authSource=admin\" \\"
    echo "     -e ME_CONFIG_BASICAUTH_USERNAME=admin \\"
    echo "     -e ME_CONFIG_BASICAUTH_PASSWORD=admin \\"
    echo "     -p 8081:8081 \\"
    echo "     mongo-express"
    echo "   Then open: http://localhost:8081"
    
    echo ""
    echo -e "${GREEN}💻 For command line:${NC}"
    echo "   mongosh \"mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/$MONGO_DB?authSource=admin\""
    
    echo ""
    echo -e "${GREEN}🎯 What to verify in UI:${NC}"
    echo "   ✅ Database '$MONGO_DB' exists"
    echo "   ✅ Collection 'test_collection' has 5 documents"
    echo "   ✅ Collection 'user_management' has 2 documents"
    echo "   ✅ Collection 'app_config' has 1 document"
    echo "   ✅ Documents contain realistic test data"
    echo "   ✅ Indexes exist on email, type, and created_at fields"
    echo "   ✅ All documents have timestamps and metadata"
}

# Function to print verification steps
print_verification_steps() {
    echo ""
    echo -e "${YELLOW}🔍 Manual Verification Steps:${NC}"
    echo -e "${YELLOW}============================${NC}"
    echo ""
    echo "1. 📱 Connect to MongoDB using your preferred UI tool"
    echo "2. 🗂️  Navigate to database: '$MONGO_DB'"
    echo "3. 📋 Verify these collections exist:"
    echo "   - test_collection (5 documents)"
    echo "   - user_management (2 documents)" 
    echo "   - app_config (1 document)"
    echo "4. 🔍 Check sample documents contain:"
    echo "   - User data with roles and metadata"
    echo "   - Service configurations"
    echo "   - Platform metrics"
    echo "   - Timestamps and version info"
    echo "5. 🏷️  Verify indexes exist on key fields"
    echo "6. ✅ Confirm all data is properly structured and readable"
    echo ""
    echo -e "${GREEN}Once verified, you can commit the MongoDB deployment!${NC}"
}

# Main execution
main() {
    # Get credentials
    if ! get_mongodb_credentials; then
        exit 1
    fi
    
    # Check port forwarding
    if ! check_port_forward; then
        exit 1
    fi
    
    # Test connectivity
    if ! test_connectivity; then
        exit 1
    fi
    
    # Create test data
    if ! create_test_data; then
        exit 1
    fi
    
    # Print connection info
    print_connection_info
    
    # Print verification steps
    print_verification_steps
    
    echo ""
    echo -e "${GREEN}🎉 MongoDB test script completed successfully!${NC}"
    echo -e "${GREEN}   Ready for manual verification with UI tools${NC}"
}

# Run main function
main "$@"
