#!/bin/bash

set -e

echo "🚀 Deploying Database Orchestrator Services..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "scripts/deploy-database-services.sh" ]; then
    print_error "Please run this script from the Nexus root directory"
    exit 1
fi

print_status "Building MongoDB Orchestrator Service..."
cd services/database/mongodb-orchestrator
docker build --no-cache -t nexus/mongodb-orchestrator:latest .
cd ../../..

print_status "Building PostgreSQL Orchestrator Service..."
cd services/database/postgresql-orchestrator
docker build --no-cache -t nexus/postgresql-orchestrator:latest .
cd ../../..

print_status "Loading images into kind cluster..."
kind load docker-image nexus/mongodb-orchestrator:latest
kind load docker-image nexus/postgresql-orchestrator:latest

print_status "Deploying MongoDB Orchestrator Service..."
kubectl apply -f iac/kubernetes/mongodb-orchestrator-deployment.yaml

print_status "Deploying PostgreSQL Orchestrator Service..."
kubectl apply -f iac/kubernetes/postgresql-orchestrator-deployment.yaml

print_status "Waiting for deployments to be ready..."
kubectl rollout status deployment/mongodb-orchestrator -n default --timeout=300s
kubectl rollout status deployment/postgresql-orchestrator -n default --timeout=300s

print_status "Checking service status..."
echo ""
echo "📊 Service Status:"
kubectl get pods -n default | grep orchestrator
echo ""

print_status "Database Orchestrator Services deployed successfully!"
echo ""
echo "🌐 Access URLs:"
echo "   MongoDB Orchestrator: http://mongodb-orchestrator.local"
echo "   PostgreSQL Orchestrator: http://postgresql-orchestrator.local"
echo ""
echo "📋 Service Endpoints:"
echo "   MongoDB Health: http://mongodb-orchestrator.local/health"
echo "   PostgreSQL Health: http://postgresql-orchestrator.local/health"
echo ""
echo "🔧 API Documentation:"
echo "   MongoDB: http://mongodb-orchestrator.local/docs"
echo "   PostgreSQL: http://postgresql-orchestrator.local/docs"
echo ""
print_status "Deployment complete! 🎉"
