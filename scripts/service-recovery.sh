#!/bin/bash

echo "🔄 Nexus Service Recovery Tool"
echo "=============================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if admin dashboard is accessible
check_admin_dashboard() {
    if curl -s http://localhost:8081/health > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to restart admin dashboard
restart_admin_dashboard() {
    echo -e "${YELLOW}🔄 Restarting Admin Dashboard...${NC}"
    
    # Delete and recreate the deployment
    kubectl delete deployment admin-dashboard --ignore-not-found=true
    sleep 5
    
    # Reapply the deployment
    kubectl apply -f services/admin-dashboard-service/kubernetes/
    
    # Wait for pod to be ready
    echo -e "${BLUE}⏳ Waiting for admin dashboard to be ready...${NC}"
    kubectl wait --for=condition=ready pod -l app=admin-dashboard --timeout=300s
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Admin Dashboard restarted successfully!${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to restart Admin Dashboard${NC}"
        return 1
    fi
}

# Function to start port forwards
start_port_forwards() {
    echo -e "${BLUE}🔌 Starting port forwards...${NC}"
    
    # Kill existing port forwards
    pkill -f "kubectl port-forward" 2>/dev/null
    sleep 2
    
    # Start all port forwards
    kubectl port-forward service/admin-dashboard-internal 8081:80 &
    kubectl port-forward service/grafana 3000:80 -n monitoring &
    kubectl port-forward service/nexus-loki 3100:3100 -n monitoring &
    kubectl port-forward service/nexus-observability-kube-p-prometheus 9090:9090 -n monitoring &
    kubectl port-forward service/nexus-observability-kube-p-alertmanager 9093:9093 -n monitoring &
    
    sleep 5
    
    echo -e "${GREEN}✅ Port forwards started!${NC}"
}

# Function to restart any service
restart_service() {
    local service_name=$1
    
    echo -e "${YELLOW}🔄 Restarting service: ${service_name}${NC}"
    
    # Scale down
    kubectl scale deployment $service_name --replicas=0
    sleep 3
    
    # Scale up
    kubectl scale deployment $service_name --replicas=1
    sleep 3
    
    # Wait for ready
    kubectl wait --for=condition=ready pod -l app=$service_name --timeout=300s
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Service ${service_name} restarted successfully!${NC}"
    else
        echo -e "${RED}❌ Failed to restart service ${service_name}${NC}"
    fi
}

# Function to show service status
show_status() {
    echo -e "${BLUE}📊 Current Service Status:${NC}"
    echo "================================"
    
    # Admin Dashboard
    if check_admin_dashboard; then
        echo -e "${GREEN}✅ Admin Dashboard: Running${NC}"
    else
        echo -e "${RED}❌ Admin Dashboard: Not accessible${NC}"
    fi
    
    # Check other services
    echo -e "\n${BLUE}Kubernetes Services:${NC}"
    kubectl get pods -l app=admin-dashboard --no-headers | while read line; do
        echo "  $line"
    done
    
    echo -e "\n${BLUE}Monitoring Services:${NC}"
    kubectl get pods -n monitoring --no-headers | while read line; do
        echo "  $line"
    done
}

# Function to show available commands
show_help() {
    echo -e "${BLUE}Available Commands:${NC}"
    echo "====================="
    echo -e "${YELLOW}  status${NC}     - Show current service status"
    echo -e "${YELLOW}  restart-admin${NC} - Restart admin dashboard"
    echo -e "${YELLOW}  restart <service>${NC} - Restart specific service"
    echo -e "${YELLOW}  start-all${NC}   - Start all port forwards"
    echo -e "${YELLOW}  help${NC}       - Show this help"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 restart-admin"
    echo "  $0 restart grafana"
    echo "  $0 start-all"
}

# Main logic
case "${1:-help}" in
    "status")
        show_status
        ;;
    "restart-admin")
        restart_admin_dashboard
        if [ $? -eq 0 ]; then
            start_port_forwards
        fi
        ;;
    "restart")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Please specify a service name${NC}"
            echo "Usage: $0 restart <service-name>"
            exit 1
        fi
        restart_service $2
        ;;
    "start-all")
        start_port_forwards
        ;;
    "help"|*)
        show_help
        ;;
esac

echo -e "\n${BLUE}Access URLs:${NC}"
echo "  📊 Admin Dashboard: http://localhost:8081"
echo "  📈 Grafana: http://localhost:3000"
echo "  📊 Prometheus: http://localhost:9090"
echo "  📝 Loki: http://localhost:3100"
echo "  🚨 Alertmanager: http://localhost:9093"
