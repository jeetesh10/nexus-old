#!/bin/bash

# Nexus Platform Startup Script
# Starts all services in the correct order

set -e

echo "🚀 Starting Nexus Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
        return 0
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${BLUE}⏳ Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts - $service_name not ready yet...${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to start within timeout${NC}"
    return 1
}

# Kill existing processes on our ports
echo -e "${BLUE}🧹 Cleaning up existing processes...${NC}"
pkill -f "python3.*api_server.py" || true
pkill -f "python3.*gateway_server.py" || true
pkill -f "python3.*landing-server.py" || true
sleep 2

# Check ports
echo -e "${BLUE}🔍 Checking port availability...${NC}"
check_port 8080 || exit 1
check_port 8081 || exit 1
check_port 8082 || exit 1
check_port 8083 || exit 1

# Start Access Control Service
echo -e "${BLUE}🔧 Starting Access Control Service...${NC}"
cd services/access-control/group-management-service
python3 api_server.py &
ACCESS_CONTROL_PID=$!
cd ../../..

# Start Auth API Service
echo -e "${BLUE}🔐 Starting Auth API Service...${NC}"
cd services/auth/auth-api-service
python3 auth_api.py &
AUTH_API_PID=$!
cd ../../..

# Wait for Access Control Service
wait_for_service "http://localhost:8083/api/health" "Access Control Service" || exit 1

# Start Landing Page Server
echo -e "${BLUE}🏠 Starting Landing Page Server...${NC}"
cd services/auth/keycloak-service
python3 landing-server.py &
LANDING_PID=$!
cd ../../..

# Wait for Landing Page Server
wait_for_service "http://localhost:8082/login.html" "Landing Page Server" || exit 1

# Start API Gateway
echo -e "${BLUE}🚪 Starting API Gateway...${NC}"
cd services/api-gateway/gateway-service
python3 gateway_server.py &
GATEWAY_PID=$!
cd ../../..

# Wait for API Gateway
wait_for_service "http://localhost:8080/health" "API Gateway" || exit 1

# Save PIDs to file for cleanup
echo $ACCESS_CONTROL_PID > /tmp/nexus_access_control.pid
echo $AUTH_API_PID > /tmp/nexus_auth_api.pid
echo $LANDING_PID > /tmp/nexus_landing.pid
echo $GATEWAY_PID > /tmp/nexus_gateway.pid

echo -e "${GREEN}🎉 Nexus Platform started successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Service URLs:${NC}"
echo -e "  🔗 API Gateway:     ${GREEN}http://localhost:8080${NC}"
echo -e "  🔐 Keycloak:        ${GREEN}http://localhost:8080/realms/nexus-platform${NC}"
echo -e "  🏠 Landing Page:    ${GREEN}http://localhost:8080/landing${NC}"
echo -e "  📊 Admin Interface: ${GREEN}http://localhost:8082/admin_interface.html${NC}"
echo -e "  🔧 Access Control:  ${GREEN}http://localhost:8083/api/health${NC}"
echo ""
echo -e "${BLUE}🧪 Test Commands:${NC}"
echo -e "  curl ${GREEN}http://localhost:8080/health${NC}"
echo -e "  curl ${GREEN}http://localhost:8080/api/services${NC}"
echo -e "  curl ${GREEN}http://localhost:8080/api/user-access?groups=nexus,platform-admin${NC}"
echo ""
echo -e "${YELLOW}💡 To stop all services: ./scripts/stop-platform.sh${NC}"
echo -e "${YELLOW}💡 To view logs: tail -f /tmp/nexus_*.log${NC}"

# Keep script running
wait
