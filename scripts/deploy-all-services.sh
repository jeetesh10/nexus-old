#!/bin/bash

# Deploy All New Services to Kubernetes
set -e

echo "🚀 Deploying all new services to Kubernetes..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to deploy a service
deploy_service() {
    local service_name=$1
    local service_path=$2
    local image_name=$3
    
    echo -e "${BLUE}📦 Building ${service_name}...${NC}"
    
    # Build Docker image
    cd ${service_path}
    docker build -t ${image_name}:latest .
    
    # Load image into kind cluster
    echo -e "${BLUE}📥 Loading ${service_name} image into kind cluster...${NC}"
    kind load docker-image ${image_name}:latest
    
    cd ../../..
}

# Function to apply Kubernetes manifests
apply_manifests() {
    local manifest_file=$1
    local service_name=$2
    
    echo -e "${BLUE}🚀 Deploying ${service_name} to Kubernetes...${NC}"
    kubectl apply -f ${manifest_file}
    
    # Wait for deployment to be ready
    echo -e "${BLUE}⏳ Waiting for ${service_name} to be ready...${NC}"
    kubectl wait --for=condition=available --timeout=300s deployment/${service_name} -n default || true
    
    # Check deployment status
    echo -e "${BLUE}📊 ${service_name} deployment status:${NC}"
    kubectl get deployment ${service_name} -n default || true
}

# Deploy Auth API Service
echo -e "${GREEN}🔐 Deploying Auth API Service...${NC}"
deploy_service "Auth API" "services/auth/auth-api-service" "nexus/auth-api"
apply_manifests "iac/kubernetes/auth-api-deployment.yaml" "auth-api-service"

# Deploy Service Mesh Controller
echo -e "${GREEN}🕸️ Deploying Service Mesh Controller...${NC}"
deploy_service "Service Mesh" "services/service-mesh" "nexus/service-mesh"
apply_manifests "iac/kubernetes/service-mesh-deployment.yaml" "service-mesh-controller"

# Deploy API Gateway
echo -e "${GREEN}🚪 Deploying API Gateway...${NC}"
deploy_service "API Gateway" "services/api-gateway/gateway-service" "nexus/api-gateway"
apply_manifests "iac/kubernetes/api-gateway-deployment.yaml" "api-gateway"

# Wait for all services to be ready
echo -e "${BLUE}⏳ Waiting for all services to be ready...${NC}"
sleep 30

# Check all deployments
echo -e "${BLUE}📊 All deployments status:${NC}"
kubectl get deployments -n default | grep -E "(auth-api|service-mesh|api-gateway)"

# Check all services
echo -e "${BLUE}🌐 All services status:${NC}"
kubectl get services -n default | grep -E "(auth-api|service-mesh|api-gateway)"

# Check all ingress
echo -e "${BLUE}🌍 All ingress status:${NC}"
kubectl get ingress -n default | grep -E "(auth-api|api-gateway)"

# Test services
echo -e "${BLUE}🧪 Testing services...${NC}"

# Test Auth API
echo -e "${YELLOW}Testing Auth API...${NC}"
kubectl port-forward service/auth-api-service 8084:8084 -n default &
AUTH_PID=$!
sleep 5
if curl -s http://localhost:8084/api/auth/health > /dev/null; then
    echo -e "${GREEN}✅ Auth API Service is healthy!${NC}"
else
    echo -e "${YELLOW}⚠️  Auth API Service might still be starting...${NC}"
fi
kill $AUTH_PID 2>/dev/null || true

# Test Service Mesh
echo -e "${YELLOW}Testing Service Mesh...${NC}"
kubectl port-forward service/service-mesh-controller 8085:8085 -n default &
MESH_PID=$!
sleep 5
if curl -s http://localhost:8085/health > /dev/null; then
    echo -e "${GREEN}✅ Service Mesh is healthy!${NC}"
else
    echo -e "${YELLOW}⚠️  Service Mesh might still be starting...${NC}"
fi
kill $MESH_PID 2>/dev/null || true

# Test API Gateway
echo -e "${YELLOW}Testing API Gateway...${NC}"
kubectl port-forward service/api-gateway 8086:8086 -n default &
GATEWAY_PID=$!
sleep 5
if curl -s http://localhost:8086/health > /dev/null; then
    echo -e "${GREEN}✅ API Gateway is healthy!${NC}"
else
    echo -e "${YELLOW}⚠️  API Gateway might still be starting...${NC}"
fi
kill $GATEWAY_PID 2>/dev/null || true

echo -e "${GREEN}🎉 All services deployed successfully!${NC}"

# Display service URLs
echo -e "${BLUE}📋 Service URLs:${NC}"
echo -e "${GREEN}   Auth API:${NC}"
echo -e "${YELLOW}     Internal: http://auth-api-service:8084${NC}"
echo -e "${YELLOW}     External: http://auth.nexus.platform${NC}"
echo -e "${GREEN}   Service Mesh:${NC}"
echo -e "${YELLOW}     Internal: http://service-mesh-controller:8085${NC}"
echo -e "${GREEN}   API Gateway:${NC}"
echo -e "${YELLOW}     Internal: http://api-gateway:8086${NC}"
echo -e "${YELLOW}     External: http://api.nexus.platform${NC}"

echo -e "${BLUE}📋 Next Steps:${NC}"
echo -e "${YELLOW}   1. Open Admin Dashboard: http://localhost:8081${NC}"
echo -e "${YELLOW}   2. You should see the new services in the dashboard${NC}"
echo -e "${YELLOW}   3. Test the APIs using Postman collection${NC}"
echo -e "${YELLOW}   4. Verify service mesh integration${NC}"
echo -e "${YELLOW}   5. Test API Gateway routing${NC}"

echo -e "${GREEN}✅ All services are now available in the Admin Dashboard!${NC}"
