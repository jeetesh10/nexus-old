#!/bin/bash
set -e

echo "🚀 Deploying Access Control Service..."

# Color functions
print_status() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# Check if we're in the right directory
if [ ! -f "scripts/deploy-access-control.sh" ]; then
    print_error "Please run this script from the Nexus project root directory"
    exit 1
fi

print_status "Building Access Control Service..."
cd services/access-control/access-control-service
docker build --no-cache -t nexus/access-control:latest .
cd ../../..

print_status "Building Landing Page Service..."
cd services/access-control/landing-page
docker build --no-cache -t nexus/landing-page:latest .
cd ../../..

print_status "Loading images into kind cluster..."
kind load docker-image nexus/access-control:latest
kind load docker-image nexus/landing-page:latest

print_status "Deploying Access Control Service..."
kubectl apply -f iac/kubernetes/access-control-deployment.yaml

print_status "Deploying Landing Page Service..."
kubectl apply -f iac/kubernetes/landing-page-deployment.yaml

print_status "Waiting for deployments to be ready..."
kubectl rollout status deployment/access-control-service -n default --timeout=300s
kubectl rollout status deployment/landing-page-service -n default --timeout=300s

print_status "Checking service status..."
echo ""
echo "📊 Service Status:"
kubectl get pods -n default | grep -E "(access-control|landing-page)"
echo ""

print_status "Access Control Service deployed successfully!"
echo ""
echo "🌐 Access URLs:"
echo "   Access Control Service: http://access-control.local"
echo "   Landing Page: http://landing-page.local"
echo ""
echo "📋 Service Endpoints:"
echo "   Access Control Health: http://access-control.local/health"
echo "   Landing Page Health: http://landing-page.local/health"
echo "   Landing Page API: http://access-control.local/api/landing-page"
echo ""
echo "🔐 Test Credentials:"
echo "   Username: admin"
echo "   Password: AdminPass123"
echo ""
print_status "Deployment complete! 🎉"
