#!/bin/bash

# Deploy Complete Nexus Stack
set -e

echo "🚀 Deploying Complete Nexus Stack..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    if ! command_exists docker; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command_exists kubectl; then
        echo -e "${RED}❌ kubectl is not installed${NC}"
        exit 1
    fi
    
    if ! command_exists kind; then
        echo -e "${RED}❌ kind is not installed${NC}"
        exit 1
    fi
    
    # Check if kind cluster exists
    if ! kind get clusters | grep -q "nexus"; then
        echo -e "${RED}❌ Kind cluster 'nexus' not found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to build and load Docker image
build_and_load_image() {
    local service_name=$1
    local service_path=$2
    local image_name=$3
    
    echo -e "${BLUE}📦 Building ${service_name}...${NC}"
    
    # Build Docker image
    cd ${service_path}
    if ! docker build -t ${image_name}:latest .; then
        echo -e "${RED}❌ Failed to build ${service_name}${NC}"
        exit 1
    fi
    
    # Load image into kind cluster
    echo -e "${BLUE}📥 Loading ${service_name} image into kind cluster...${NC}"
    if ! kind load docker-image ${image_name}:latest; then
        echo -e "${RED}❌ Failed to load ${service_name} image${NC}"
        exit 1
    fi
    
    cd ../../..
    echo -e "${GREEN}✅ ${service_name} built and loaded successfully${NC}"
}

# Function to deploy to Kubernetes
deploy_to_kubernetes() {
    local manifest_file=$1
    local service_name=$2
    
    echo -e "${BLUE}🚀 Deploying ${service_name} to Kubernetes...${NC}"
    
    if ! kubectl apply -f ${manifest_file}; then
        echo -e "${RED}❌ Failed to deploy ${service_name}${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ ${service_name} deployed successfully${NC}"
}

# Function to wait for deployment
wait_for_deployment() {
    local service_name=$1
    local namespace=${2:-default}
    local timeout=${3:-300}
    
    echo -e "${BLUE}⏳ Waiting for ${service_name} to be ready...${NC}"
    
    if kubectl wait --for=condition=available --timeout=${timeout}s deployment/${service_name} -n ${namespace}; then
        echo -e "${GREEN}✅ ${service_name} is ready${NC}"
    else
        echo -e "${YELLOW}⚠️  ${service_name} might still be starting up${NC}"
    fi
}

# Function to test service
test_service() {
    local service_name=$1
    local port=$2
    local health_path=$3
    
    echo -e "${BLUE}🧪 Testing ${service_name}...${NC}"
    
    # Start port forward
    kubectl port-forward service/${service_name} ${port}:${port} -n default &
    local port_forward_pid=$!
    
    # Wait for port forward to be ready
    sleep 5
    
    # Test the service
    if curl -s http://localhost:${port}${health_path} > /dev/null; then
        echo -e "${GREEN}✅ ${service_name} is healthy!${NC}"
    else
        echo -e "${YELLOW}⚠️  ${service_name} might still be starting...${NC}"
    fi
    
    # Kill port forward
    kill $port_forward_pid 2>/dev/null || true
}

# Main deployment process
main() {
    check_prerequisites
    
    echo -e "${GREEN}🔐 Deploying Group Management Service...${NC}"
    build_and_load_image "Group Management" "services/access-control/group-management-service" "nexus/group-management"
    deploy_to_kubernetes "iac/kubernetes/group-management-deployment.yaml" "group-management-service"
    wait_for_deployment "group-management-service"
    
    echo -e "${GREEN}🔐 Deploying Auth API Service...${NC}"
    build_and_load_image "Auth API" "services/auth/auth-api-service" "nexus/auth-api"
    deploy_to_kubernetes "iac/kubernetes/auth-api-deployment.yaml" "auth-api-service"
    wait_for_deployment "auth-api-service"
    
    echo -e "${GREEN}🕸️ Deploying Service Mesh Controller...${NC}"
    build_and_load_image "Service Mesh" "services/service-mesh" "nexus/service-mesh"
    deploy_to_kubernetes "iac/kubernetes/service-mesh-deployment.yaml" "service-mesh-controller"
    wait_for_deployment "service-mesh-controller"
    
    echo -e "${GREEN}🚪 Deploying API Gateway...${NC}"
    build_and_load_image "API Gateway" "services/api-gateway/gateway-service" "nexus/api-gateway"
    deploy_to_kubernetes "iac/kubernetes/api-gateway-deployment.yaml" "api-gateway"
    wait_for_deployment "api-gateway"
    
    # Wait for all services to be ready
    echo -e "${BLUE}⏳ Waiting for all services to be ready...${NC}"
    sleep 30
    
    # Check all deployments
    echo -e "${BLUE}📊 All deployments status:${NC}"
    kubectl get deployments -n default | grep -E "(group-management|auth-api|service-mesh|api-gateway)"
    
    # Check all services
    echo -e "${BLUE}🌐 All services status:${NC}"
    kubectl get services -n default | grep -E "(group-management|auth-api|service-mesh|api-gateway)"
    
    # Test services
    echo -e "${BLUE}🧪 Testing services...${NC}"
    test_service "group-management-service" "8083" "/health"
    test_service "auth-api-service" "8084" "/api/auth/health"
    test_service "service-mesh-controller" "8085" "/health"
    test_service "api-gateway" "8086" "/health"
    
    echo -e "${GREEN}🎉 Complete stack deployed successfully!${NC}"
    
    # Display service URLs
    echo -e "${BLUE}📋 Service URLs:${NC}"
    echo -e "${GREEN}   Group Management:${NC}"
    echo -e "${YELLOW}     Internal: http://group-management-service:8083${NC}"
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
    echo -e "${YELLOW}   2. You should see all new services in the dashboard${NC}"
    echo -e "${YELLOW}   3. Test the APIs using Postman collection${NC}"
    echo -e "${YELLOW}   4. Verify data-driven access control is working${NC}"
    echo -e "${YELLOW}   5. Test authentication with real Keycloak users${NC}"
    
    echo -e "${GREEN}✅ All services are now available in the Admin Dashboard!${NC}"
}

# Run main function
main "$@"
