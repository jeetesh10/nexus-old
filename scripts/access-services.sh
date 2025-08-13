#!/bin/bash

echo "🚀 Nexus Platform Service Access"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to start port-forward
start_port_forward() {
    local service_name=$1
    local local_port=$2
    local target_port=$3
    local namespace=$4
    
    echo -e "${YELLOW}Starting port-forward for $service_name...${NC}"
    kubectl port-forward service/$service_name $local_port:$target_port -n $namespace > /dev/null 2>&1 &
    echo -e "${GREEN}✅ $service_name accessible at http://localhost:$local_port${NC}"
}

# Kill any existing port-forwards
echo -e "${YELLOW}Stopping any existing port-forwards...${NC}"
pkill -f "kubectl port-forward" 2>/dev/null
sleep 2

# Start port-forwards for all services
echo -e "\n${BLUE}Starting service access...${NC}"

# Admin Dashboard
start_port_forward "admin-dashboard-internal" 8081 80 "default"

# Grafana
start_port_forward "grafana" 3000 80 "monitoring"

# Loki
start_port_forward "nexus-loki" 3100 3100 "monitoring"

# Prometheus
start_port_forward "nexus-observability-kube-p-prometheus" 9090 9090 "monitoring"

# Alertmanager
start_port_forward "nexus-observability-kube-p-alertmanager" 9093 9093 "monitoring"

echo -e "\n${GREEN}🎉 All services are now accessible!${NC}"
echo -e "\n${YELLOW}Service URLs:${NC}"
echo -e "${GREEN}📊 Admin Dashboard API:${NC} http://localhost:8081"
echo -e "${GREEN}📈 Grafana:${NC} http://localhost:3000 (admin/admin)"
echo -e "${GREEN}📝 Loki:${NC} http://localhost:3100"
echo -e "${GREEN}📊 Prometheus:${NC} http://localhost:9090"
echo -e "${GREEN}🚨 Alertmanager:${NC} http://localhost:9093"
echo -e "\n${YELLOW}API Endpoints:${NC}"
echo -e "  GET http://localhost:8080/api/services"
echo -e "  POST http://localhost:8080/api/services/{name}/stop"
echo -e "  POST http://localhost:8080/api/services/{name}/start"
echo -e "\n${YELLOW}To stop all port-forwards:${NC} pkill -f 'kubectl port-forward'"
echo -e "\n${YELLOW}Press Ctrl+C to stop this script${NC}"

# Keep the script running
while true; do
    sleep 10
    # Check if port-forwards are still running
    if ! pgrep -f "kubectl port-forward" > /dev/null; then
        echo -e "\n${YELLOW}⚠️  Port-forwards stopped. Restarting...${NC}"
        # Restart port-forwards
        start_port_forward "admin-dashboard-internal" 8081 80 "default"
        start_port_forward "grafana" 3000 80 "monitoring"
        start_port_forward "nexus-loki" 3100 3100 "monitoring"
        start_port_forward "nexus-observability-kube-p-prometheus" 9090 9090 "monitoring"
        start_port_forward "nexus-observability-kube-p-alertmanager" 9093 9093 "monitoring"
    fi
done
