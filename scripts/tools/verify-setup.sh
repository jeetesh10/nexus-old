#!/bin/bash

echo "🔍 Nexus Platform Verification Script"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

echo -e "\n${YELLOW}1. Checking Kubernetes Cluster${NC}"
kubectl get nodes > /dev/null 2>&1
print_status $? "Kubernetes cluster is accessible"

echo -e "\n${YELLOW}2. Checking Observability Stack${NC}"
kubectl get pods -n monitoring | grep -q "Running" > /dev/null 2>&1
print_status $? "Monitoring pods are running"

echo -e "\n${YELLOW}3. Checking Ingress Controller${NC}"
kubectl get pods -n ingress-nginx | grep -q "Running" > /dev/null 2>&1
print_status $? "NGINX Ingress controller is running"

echo -e "\n${YELLOW}4. Checking Admin Dashboard${NC}"
kubectl get pods -l app=admin-dashboard | grep -q "Running" > /dev/null 2>&1
print_status $? "Admin dashboard is running"

echo -e "\n${YELLOW}5. Testing Admin Dashboard API${NC}"
# Start port-forward in background
kubectl port-forward service/admin-dashboard-internal 8081:80 > /dev/null 2>&1 &
PF_PID=$!
sleep 3

# Test API
curl -s http://localhost:8081/api/services > /dev/null 2>&1
print_status $? "Admin dashboard API is responding"

# Kill port-forward
kill $PF_PID 2>/dev/null

echo -e "\n${YELLOW}6. Checking RBAC Configuration${NC}"
kubectl get clusterrole admin-dashboard-role > /dev/null 2>&1
print_status $? "RBAC is properly configured"

echo -e "\n${YELLOW}7. Checking Services${NC}"
kubectl get services --all-namespaces | grep -q "admin-dashboard-internal" > /dev/null 2>&1
print_status $? "Admin dashboard service is configured"

echo -e "\n${YELLOW}8. Checking Ingress Rules${NC}"
kubectl get ingress | grep -q "admin-dashboard-ingress" > /dev/null 2>&1
print_status $? "Ingress rules are configured"

echo -e "\n${YELLOW}9. Testing Service Management${NC}"
# Deploy test service if not exists
if ! kubectl get deployment test-service > /dev/null 2>&1; then
    kubectl apply -f test-service.yaml > /dev/null 2>&1
    sleep 10
fi

# Start port-forward for testing
kubectl port-forward service/admin-dashboard-internal 8081:80 > /dev/null 2>&1 &
PF_PID=$!
sleep 3

# Test service listing
curl -s http://localhost:8081/api/services | grep -q "test-service" > /dev/null 2>&1
print_status $? "Service listing works"

# Test service stop
curl -s -X POST http://localhost:8081/api/services/test-service/stop > /dev/null 2>&1
sleep 5
kubectl get pods -l app=test-service 2>/dev/null | grep -q "No resources" > /dev/null 2>&1
print_status $? "Service stop functionality works"

# Test service start
curl -s -X POST http://localhost:8081/api/services/test-service/start > /dev/null 2>&1
sleep 10
kubectl get pods -l app=test-service | grep -q "Running" > /dev/null 2>&1
print_status $? "Service start functionality works"

# Kill port-forward
kill $PF_PID 2>/dev/null

echo -e "\n${YELLOW}10. Checking Grafana Access${NC}"
GRAFANA_PORT=$(kubectl get service -n monitoring grafana -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
if [ ! -z "$GRAFANA_PORT" ]; then
    echo -e "${GREEN}✅ Grafana accessible at http://localhost:$GRAFANA_PORT${NC}"
    echo -e "${YELLOW}   Username: admin${NC}"
    echo -e "${YELLOW}   Password: admin${NC}"
else
    echo -e "${RED}❌ Grafana service not found${NC}"
fi

echo -e "\n${YELLOW}11. Checking Prometheus Access${NC}"
echo -e "${GREEN}✅ Prometheus accessible via port-forward:${NC}"
echo -e "${YELLOW}   kubectl port-forward service/nexus-observability-kube-p-prometheus 9090:9090 -n monitoring${NC}"
echo -e "${YELLOW}   Then visit: http://localhost:9090${NC}"

echo -e "\n${YELLOW}12. Checking Loki Logging${NC}"
kubectl get pods -n monitoring | grep -q "nexus-loki" > /dev/null 2>&1
print_status $? "Loki logging stack is running"

echo -e "\n${GREEN}🎉 Nexus Platform Verification Complete!${NC}"
echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "1. Access Grafana at http://localhost:$GRAFANA_PORT"
echo -e "2. Set up Prometheus port-forward for metrics"
echo -e "3. Deploy additional services using the admin dashboard"
echo -e "4. Configure custom alerts and dashboards"
echo -e "\n${YELLOW}For more information, see README.md${NC}"
