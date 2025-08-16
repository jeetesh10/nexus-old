#!/bin/bash

echo "🚀 Starting Nexus Unified Dashboard"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Kill any existing port-forwards
echo -e "${YELLOW}Stopping any existing port-forwards...${NC}"
pkill -f "kubectl port-forward" 2>/dev/null
sleep 2

# Start all port-forwards
echo -e "${BLUE}Starting port-forwards for all services...${NC}"

kubectl port-forward service/admin-dashboard-internal 8081:80 &
kubectl port-forward service/grafana 3000:80 -n monitoring &
kubectl port-forward service/nexus-loki 3100:3100 -n monitoring &
kubectl port-forward service/nexus-observability-kube-p-prometheus 9090:9090 -n monitoring &
kubectl port-forward service/nexus-observability-kube-p-alertmanager 9093:9093 -n monitoring &

# Wait for port-forwards to start
sleep 5

echo -e "\n${GREEN}🎉 Nexus Unified Dashboard is ready!${NC}"
echo -e "\n${YELLOW}Access your unified dashboard at:${NC}"
echo -e "${GREEN}🌐 http://localhost:8081${NC}"
echo -e "\n${YELLOW}This single URL gives you access to:${NC}"
echo -e "  📊 Services Management (main tab)"
echo -e "  📈 Grafana Dashboards"
echo -e "  📊 Prometheus Metrics"
echo -e "  📝 Loki Logs"
echo -e "  🚨 Alertmanager"
echo -e "  🔧 API Documentation"
echo -e "\n${YELLOW}Individual service URLs (if needed):${NC}"
echo -e "  📈 Grafana: http://localhost:3000"
echo -e "  📊 Prometheus: http://localhost:9090"
echo -e "  📝 Loki: http://localhost:3100"
echo -e "  🚨 Alertmanager: http://localhost:9093"
echo -e "\n${YELLOW}To stop all services:${NC} pkill -f 'kubectl port-forward'"
echo -e "\n${BLUE}Press Ctrl+C to stop this script${NC}"

# Keep the script running
while true; do
    sleep 10
    # Check if port-forwards are still running
    if ! pgrep -f "kubectl port-forward" > /dev/null; then
        echo -e "\n${YELLOW}⚠️  Port-forwards stopped. Restarting...${NC}"
        # Restart port-forwards
        kubectl port-forward service/admin-dashboard-internal 8081:80 &
        kubectl port-forward service/grafana 3000:80 -n monitoring &
        kubectl port-forward service/nexus-loki 3100:3100 -n monitoring &
        kubectl port-forward service/nexus-observability-kube-p-prometheus 9090:9090 -n monitoring &
        kubectl port-forward service/nexus-observability-kube-p-alertmanager 9093:9093 -n monitoring &
        sleep 5
    fi
done
