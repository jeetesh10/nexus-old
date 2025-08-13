#!/bin/bash

# Nexus Platform Stop Script
# Stops all running services

echo "🛑 Stopping Nexus Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to kill process by PID file
kill_service() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${BLUE}🛑 Stopping $service_name (PID: $pid)...${NC}"
            kill $pid
            sleep 2
            
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  Force killing $service_name...${NC}"
                kill -9 $pid
            fi
            
            echo -e "${GREEN}✅ $service_name stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  PID file not found for $service_name${NC}"
    fi
}

# Kill services by PID files
kill_service "/tmp/nexus_access_control.pid" "Access Control Service"
kill_service "/tmp/nexus_auth_api.pid" "Auth API Service"
kill_service "/tmp/nexus_landing.pid" "Landing Page Server"
kill_service "/tmp/nexus_gateway.pid" "API Gateway"

# Kill any remaining processes by pattern
echo -e "${BLUE}🧹 Cleaning up any remaining processes...${NC}"
pkill -f "python3.*api_server.py" || true
pkill -f "python3.*auth_api.py" || true
pkill -f "python3.*gateway_server.py" || true
pkill -f "python3.*landing-server.py" || true

# Wait a moment for processes to stop
sleep 2

# Check if ports are free
echo -e "${BLUE}🔍 Checking if ports are free...${NC}"
ports=(8080 8081 8082 8083 8084)

for port in "${ports[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is still in use${NC}"
    else
        echo -e "${GREEN}✅ Port $port is free${NC}"
    fi
done

echo -e "${GREEN}🎉 Nexus Platform stopped successfully!${NC}"
