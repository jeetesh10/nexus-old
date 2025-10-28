#!/bin/bash

# Deploy Auth API Service to Kubernetes
set -e

echo "🚀 Building and deploying Auth API Service..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="auth-api-service"
IMAGE_NAME="nexus/auth-api"
IMAGE_TAG="latest"
NAMESPACE="default"

echo -e "${BLUE}📦 Building Docker image...${NC}"

# Build Docker image
cd services/auth/auth-api-service
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

# Load image into kind cluster
echo -e "${BLUE}📥 Loading image into kind cluster...${NC}"
kind load docker-image ${IMAGE_NAME}:${IMAGE_TAG}

# Deploy to Kubernetes
echo -e "${BLUE}🚀 Deploying to Kubernetes...${NC}"
cd ../../..
kubectl apply -f iac/kubernetes/auth-api-deployment.yaml

# Wait for deployment to be ready
echo -e "${BLUE}⏳ Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/${SERVICE_NAME} -n ${NAMESPACE}

# Check deployment status
echo -e "${BLUE}📊 Checking deployment status...${NC}"
kubectl get deployment ${SERVICE_NAME} -n ${NAMESPACE}

# Get service URL
echo -e "${BLUE}🌐 Service URLs:${NC}"
echo -e "${GREEN}   Internal: http://${SERVICE_NAME}:8084${NC}"
echo -e "${GREEN}   External: http://auth.nexus.platform${NC}"

# Test the service
echo -e "${BLUE}🧪 Testing service...${NC}"
sleep 10
kubectl port-forward service/${SERVICE_NAME} 8084:8084 -n ${NAMESPACE} &
PORT_FORWARD_PID=$!

sleep 5
if curl -s http://localhost:8084/api/auth/health > /dev/null; then
    echo -e "${GREEN}✅ Auth API Service is running and healthy!${NC}"
else
    echo -e "${YELLOW}⚠️  Service might still be starting up...${NC}"
fi

# Kill port forward
kill $PORT_FORWARD_PID 2>/dev/null || true

echo -e "${GREEN}🎉 Auth API Service deployed successfully!${NC}"
echo -e "${BLUE}📋 Next Steps:${NC}"
echo -e "${YELLOW}   1. Check the Admin Dashboard to see the new service${NC}"
echo -e "${YELLOW}   2. Test the API endpoints using Postman${NC}"
echo -e "${YELLOW}   3. Verify service mesh integration${NC}"
