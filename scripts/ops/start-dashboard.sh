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

# Determine dashboard local port (default 8081)
DASHBOARD_LOCAL_PORT=${DASHBOARD_LOCAL_PORT:-8081}

# Preflight: check if desired port is free (prefer ss; fallback to lsof)
PORT_IN_USE=0
if command -v ss >/dev/null 2>&1; then
    if ss -ltn | awk '{print $4}' | grep -q ":$DASHBOARD_LOCAL_PORT$"; then PORT_IN_USE=1; fi
elif command -v lsof >/dev/null 2>&1; then
    if lsof -Pi :$DASHBOARD_LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then PORT_IN_USE=1; fi
fi

if [ "$PORT_IN_USE" = "1" ]; then
    echo -e "${YELLOW}Port $DASHBOARD_LOCAL_PORT is already in use.${NC}"
    # If default 8081 is used by mongo-express locally, hint the fix
    if [ "$DASHBOARD_LOCAL_PORT" = "8081" ]; then
        echo -e "${YELLOW}Tip:${NC} If you're running local mongo-express, prefer mapping it to 8082 (host) instead."
        echo -e "${YELLOW}You can also override the admin dashboard port:${NC} DASHBOARD_LOCAL_PORT=18081 $0"
    fi
    # Try an automatic fall-back to 18081
    ALT_PORT=18081
    ALT_IN_USE=0
    if command -v ss >/dev/null 2>&1; then
        if ss -ltn | awk '{print $4}' | grep -q ":$ALT_PORT$"; then ALT_IN_USE=1; fi
    elif command -v lsof >/dev/null 2>&1; then
        if lsof -Pi :$ALT_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then ALT_IN_USE=1; fi
    fi
    if [ "$ALT_IN_USE" = "0" ]; then
        echo -e "${BLUE}Falling back to port $ALT_PORT for the dashboard...${NC}"
        DASHBOARD_LOCAL_PORT=$ALT_PORT
    else
        echo -e "${YELLOW}No free fallback port found automatically. Please free a port or set DASHBOARD_LOCAL_PORT.<${NC}"
    fi
fi

# Start all port-forwards
echo -e "${BLUE}Starting port-forwards for all services...${NC}"

# Forward Admin Dashboard only if service exists
if kubectl get svc admin-dashboard-internal >/dev/null 2>&1; then
    kubectl port-forward service/admin-dashboard-internal ${DASHBOARD_LOCAL_PORT}:80 &
else
    echo -e "${YELLOW}service/admin-dashboard-internal not found. Ensure the admin dashboard is deployed.${NC}"
fi
# Port-forward monitoring stack if present
kubectl get svc grafana -n monitoring >/dev/null 2>&1 && kubectl port-forward service/grafana 3000:80 -n monitoring &
kubectl get svc nexus-loki -n monitoring >/dev/null 2>&1 && kubectl port-forward service/nexus-loki 3100:3100 -n monitoring &
kubectl get svc nexus-observability-kube-p-prometheus -n monitoring >/dev/null 2>&1 && kubectl port-forward service/nexus-observability-kube-p-prometheus 9090:9090 -n monitoring &
kubectl get svc nexus-observability-kube-p-alertmanager -n monitoring >/dev/null 2>&1 && kubectl port-forward service/nexus-observability-kube-p-alertmanager 9093:9093 -n monitoring &
# Keycloak (so browser keycloak-js can reach it via localhost:9080)
kubectl port-forward service/keycloak-service 9080:8080 &

# Wait for admin dashboard port-forward to become ready
for i in {1..10}; do
    if command -v ss >/dev/null 2>&1; then
        ss -ltn | awk '{print $4}' | grep -q ":$DASHBOARD_LOCAL_PORT$" && break
    else
        nc -z localhost $DASHBOARD_LOCAL_PORT >/dev/null 2>&1 && break
    fi
    sleep 0.5
done

echo -e "\n${GREEN}🎉 Nexus Unified Dashboard is ready!${NC}"
echo -e "\n${YELLOW}Access your unified dashboard at:${NC}"
echo -e "${GREEN}🌐 Landing page:${NC} http://localhost:${DASHBOARD_LOCAL_PORT}/"
echo -e "${GREEN}🛡️  Admin dashboard:${NC} http://localhost:${DASHBOARD_LOCAL_PORT}/admin"
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
echo -e "  🗄️  Mongo Express (local optional): http://localhost:8082"
echo -e "\n${YELLOW}Note:${NC} Keycloak is available via the same host at ${BLUE}/keycloak/${NC}. The 9080 forward is for seeding/scripts only."
echo -e "\n${YELLOW}To stop all services:${NC} pkill -f 'kubectl port-forward'"
echo -e "\n${BLUE}Press Ctrl+C to stop this script${NC}"

# Keep the script running
while true; do
    sleep 10
    # Check if port-forwards are still running
    if ! pgrep -f "kubectl port-forward" > /dev/null; then
        echo -e "\n${YELLOW}⚠️  Port-forwards stopped. Restarting...${NC}"
        # Restart port-forwards
    kubectl port-forward service/admin-dashboard-internal ${DASHBOARD_LOCAL_PORT}:80 &
        kubectl port-forward service/grafana 3000:80 -n monitoring &
        kubectl port-forward service/nexus-loki 3100:3100 -n monitoring &
        kubectl port-forward service/nexus-observability-kube-p-prometheus 9090:9090 -n monitoring &
        kubectl port-forward service/nexus-observability-kube-p-alertmanager 9093:9093 -n monitoring &
        kubectl port-forward service/keycloak-service 9080:8080 &
        sleep 5
    fi
done
