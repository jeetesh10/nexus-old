#!/bin/bash
set -euo pipefail

# Auth API Service Deployment Script
# ==================================
# Deploys the Auth API service to the Nexus platform

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[AUTH-API]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[AUTH-API]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[AUTH-API]${NC} $1"
}

log_error() {
    echo -e "${RED}[AUTH-API]${NC} $1"
}

# Configuration
WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVICE_DIR="${WORKSPACE_ROOT}/services/auth-api-service"
NAMESPACE="nexus-platform"

# Check if Docker is running
check_docker() {
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Check if kubectl is available and cluster is accessible
check_kubernetes() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Unable to connect to Kubernetes cluster"
        exit 1
    fi
}

# Create namespace if it doesn't exist
ensure_namespace() {
    log_info "Ensuring namespace '$NAMESPACE' exists..."
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
}

# Build Docker image
build_image() {
    log_info "Building Auth API service Docker image..."
    
    cd "$SERVICE_DIR"
    
    # Build the image
    docker build -t auth-api-service:latest .
    
    if [[ $? -eq 0 ]]; then
        log_success "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Deploy Keycloak credentials secret
deploy_secrets() {
    log_info "Ensuring Keycloak credentials secret exists..."
    
    # Check if secret exists in keycloak namespace
    if kubectl get secret keycloak-credentials -n keycloak &> /dev/null; then
        # Copy secret to nexus-platform namespace
        kubectl get secret keycloak-credentials -n keycloak -o yaml | \
        sed "s/namespace: keycloak/namespace: $NAMESPACE/" | \
        kubectl apply -f -
        
        log_success "Keycloak credentials secret deployed"
    else
        log_warn "Keycloak credentials secret not found in keycloak namespace"
        log_info "Creating default credentials secret..."
        
        kubectl create secret generic keycloak-credentials \
            --from-literal=admin-username=temp-admin \
            --from-literal=admin-password=Test@1234 \
            -n "$NAMESPACE" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
}

# Deploy Auth API service
deploy_auth_api() {
    log_info "Deploying Auth API service..."
    
    cd "$SERVICE_DIR"
    
    # Apply Kubernetes manifests
    kubectl apply -f kubernetes/deployment.yaml
    
    if [[ $? -eq 0 ]]; then
        log_success "Auth API service deployed successfully"
    else
        log_error "Failed to deploy Auth API service"
        exit 1
    fi
}

# Wait for deployment to be ready
wait_for_deployment() {
    log_info "Waiting for Auth API service to be ready..."
    
    kubectl rollout status deployment/auth-api-service -n "$NAMESPACE" --timeout=300s
    
    if [[ $? -eq 0 ]]; then
        log_success "Auth API service is ready"
    else
        log_error "Auth API service failed to become ready"
        exit 1
    fi
}

# Setup port forwarding
setup_port_forward() {
    log_info "Setting up port forwarding..."
    
    # Kill existing port forwards
    pkill -f "kubectl port-forward.*auth-api-service.*8085" || true
    sleep 2
    
    # Start new port forward in background
    kubectl port-forward svc/auth-api-service -n "$NAMESPACE" 8085:8085 > /dev/null 2>&1 &
    
    if [[ $? -eq 0 ]]; then
        log_success "Port forwarding setup: http://localhost:8085"
        log_info "Swagger UI available at: http://localhost:8085/docs"
    else
        log_warn "Failed to setup port forwarding"
    fi
}

# Test Auth API service
test_auth_api() {
    log_info "Testing Auth API service..."
    
    # Wait a moment for port forward to be ready
    sleep 3
    
    # Test health endpoint
    if curl -s http://localhost:8085/api/auth/health > /dev/null; then
        log_success "Auth API service is responding"
        
        # Show service info
        echo ""
        echo "🚀 Auth API Service Status:"
        echo "  Health: http://localhost:8085/api/auth/health"
        echo "  Swagger UI: http://localhost:8085/docs"
        echo "  Service running in namespace: $NAMESPACE"
        echo ""
    else
        log_warn "Auth API service health check failed"
        log_info "Service may still be starting up. Check status with: kubectl get pods -n $NAMESPACE"
    fi
}

# Cleanup Auth API service
cleanup_auth_api() {
    log_info "Cleaning up Auth API service..."
    
    # Stop port forwarding
    pkill -f "kubectl port-forward.*auth-api-service.*8085" || true
    
    # Delete Kubernetes resources
    cd "$SERVICE_DIR"
    kubectl delete -f kubernetes/deployment.yaml --ignore-not-found=true
    
    log_success "Auth API service cleanup completed"
}

# Show deployment status
show_status() {
    echo ""
    echo "Auth API Service Status:"
    echo "======================="
    
    # Check deployment
    if kubectl get deployment auth-api-service -n "$NAMESPACE" &> /dev/null; then
        echo -e "✅ Deployment: ${GREEN}EXISTS${NC}"
        
        # Check if pods are running
        local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app=auth-api-service --field-selector=status.phase=Running -o name | wc -l)
        local total_pods=$(kubectl get pods -n "$NAMESPACE" -l app=auth-api-service -o name | wc -l)
        
        if [[ $ready_pods -eq $total_pods ]] && [[ $total_pods -gt 0 ]]; then
            echo -e "✅ Pods: ${GREEN}$ready_pods/$total_pods RUNNING${NC}"
        else
            echo -e "❌ Pods: ${RED}$ready_pods/$total_pods RUNNING${NC}"
        fi
    else
        echo -e "❌ Deployment: ${RED}NOT FOUND${NC}"
    fi
    
    # Check service
    if kubectl get service auth-api-service -n "$NAMESPACE" &> /dev/null; then
        echo -e "✅ Service: ${GREEN}EXISTS${NC}"
    else
        echo -e "❌ Service: ${RED}NOT FOUND${NC}"
    fi
    
    # Check port forwarding
    if pgrep -f "kubectl port-forward.*auth-api-service.*8085" > /dev/null; then
        echo -e "✅ Port Forward: ${GREEN}ACTIVE (http://localhost:8085)${NC}"
    else
        echo -e "❌ Port Forward: ${RED}INACTIVE${NC}"
    fi
    
    echo ""
}

# Print usage
usage() {
    cat << EOF
Auth API Service Deployment Script

USAGE:
    $0 [OPTION]

OPTIONS:
    --deploy-auth-api    Build and deploy Auth API service
    --cleanup           Remove Auth API service
    --status            Show deployment status
    --port-forward      Setup port forwarding only
    --test              Test Auth API service
    --help              Show this help

EXAMPLES:
    $0 --deploy-auth-api    # Full deployment
    $0 --status             # Check status
    $0 --cleanup            # Remove service

EOF
}

# Main execution
main() {
    local action="${1:-help}"
    
    case "$action" in
        "--deploy-auth-api")
            check_docker
            check_kubernetes
            ensure_namespace
            build_image
            deploy_secrets
            deploy_auth_api
            wait_for_deployment
            setup_port_forward
            test_auth_api
            show_status
            ;;
        "--cleanup")
            check_kubernetes
            cleanup_auth_api
            ;;
        "--status")
            check_kubernetes
            show_status
            ;;
        "--port-forward")
            check_kubernetes
            setup_port_forward
            ;;
        "--test")
            test_auth_api
            ;;
        "--help"|"help")
            usage
            ;;
        *)
            log_error "Unknown option: $action"
            echo ""
            usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
