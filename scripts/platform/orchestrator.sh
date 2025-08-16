#!/bin/bash
set -euo pipefail

# Nexus Platform Orchestrator
# ===========================
# Simple orchestrator that calls our modular deployment scripts in proper sequence

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo ""
    echo "================================"
    echo "$1"
    echo "================================"
}

# Configuration
WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEPLOY_DIR="${WORKSPACE_ROOT}/scripts/deploy"
UTILS_DIR="${WORKSPACE_ROOT}/scripts/utils"

# Print usage
usage() {
    cat << EOF
Nexus Platform Orchestrator

USAGE:
    $0 COMMAND

COMMANDS:
    deploy-all          Deploy entire platform (core + databases)
    deploy-core         Deploy core platform only (Keycloak)
    deploy-databases    Deploy all databases (MongoDB + Neo4j)
    
    status             Show status of all services
    test-all           Run tests for all services
    
    cleanup-all        Clean up entire platform
    cleanup-databases  Clean up only databases
    
    help               Show this help

SEQUENCE:
    1. Core platform setup (Vault, External Secrets, Linkerd)
    2. Keycloak (Identity Management)
    3. MongoDB (Document Database)
    4. Neo4j (Graph Database)
    5. PostgreSQL (coming soon)

EXAMPLES:
    $0 deploy-all      # Deploy everything
    $0 status          # Check what's running
    $0 test-all        # Test all services
    $0 cleanup-all     # Clean everything

EOF
}

# Check if we have the required scripts
check_scripts() {
    local required_scripts=(
        "$DEPLOY_DIR/platform-keycloak.sh"
        "$DEPLOY_DIR/platform-mongodb.sh"
        "$DEPLOY_DIR/platform-neo4j.sh"
        "$UTILS_DIR/verify-setup.sh"
    )
    
    for script in "${required_scripts[@]}"; do
        if [[ ! -f "$script" ]]; then
            log_error "Required script not found: $script"
            exit 1
        fi
    done
}

# Deploy core platform
deploy_core() {
    log_header "Deploying Core Platform"
    
    log_info "Step 1: Setting up core infrastructure (Vault, External Secrets, Linkerd)..."
    bash "$UTILS_DIR/verify-setup.sh"
    
    log_info "Step 2: Deploying Keycloak..."
    bash "$DEPLOY_DIR/platform-keycloak.sh" --deploy-keycloak
    
    log_success "Core platform deployment completed!"
}

# Deploy databases
deploy_databases() {
    log_header "Deploying Database Services"
    
    log_info "Step 1: Deploying MongoDB..."
    bash "$DEPLOY_DIR/platform-mongodb.sh" --deploy-mongodb
    
    log_info "Step 2: Deploying Neo4j..."
    bash "$DEPLOY_DIR/platform-neo4j.sh" --deploy-neo4j
    
    log_success "Database deployment completed!"
}

# Deploy everything
deploy_all() {
    log_header "Deploying Complete Nexus Platform"
    
    deploy_core
    echo ""
    deploy_databases
    
    log_success "Complete platform deployment finished!"
    show_status
}

# Show platform status
show_status() {
    log_header "Platform Status"
    
    echo "Core Infrastructure:"
    echo "-------------------"
    
    # Check Vault
    if kubectl get svc vault -n nexus-platform &> /dev/null; then
        echo -e "✅ Vault: ${GREEN}RUNNING${NC}"
    else
        echo -e "❌ Vault: ${RED}STOPPED${NC}"
    fi
    
    # Check External Secrets
    if kubectl get deployment external-secrets-operator -n external-secrets &> /dev/null; then
        echo -e "✅ External Secrets: ${GREEN}RUNNING${NC}"
    else
        echo -e "❌ External Secrets: ${RED}STOPPED${NC}"
    fi
    
    # Check Linkerd
    if kubectl get deployment linkerd-controller -n linkerd &> /dev/null; then
        echo -e "✅ Linkerd: ${GREEN}RUNNING${NC}"
    else
        echo -e "❌ Linkerd: ${RED}STOPPED${NC}"
    fi
    
    echo ""
    echo "Application Services:"
    echo "--------------------"
    
    # Check Keycloak
    if kubectl get pod -n keycloak -l app=keycloak --field-selector=status.phase=Running &> /dev/null; then
        echo -e "✅ Keycloak: ${GREEN}RUNNING${NC} (http://localhost:8080)"
    else
        echo -e "❌ Keycloak: ${RED}STOPPED${NC}"
    fi
    
    echo ""
    echo "Database Services:"
    echo "-----------------"
    
    # Check MongoDB
    if kubectl get pod mongodb-0 -n mongodb 2>/dev/null | grep -q "Running"; then
        echo -e "✅ MongoDB: ${GREEN}RUNNING${NC} (mongodb://localhost:27017)"
        if kubectl get pod -n mongodb -l app=mongo-express 2>/dev/null | grep -q "Running"; then
            echo -e "✅ Mongo Express: ${GREEN}RUNNING${NC} (http://localhost:8081)"
        fi
    else
        echo -e "❌ MongoDB: ${RED}STOPPED${NC}"
    fi
    
    # Check Neo4j
    if kubectl get pod neo4j-0 -n neo4j 2>/dev/null | grep -q "Running"; then
        echo -e "✅ Neo4j: ${GREEN}RUNNING${NC} (http://localhost:7474, bolt://localhost:7687)"
    else
        echo -e "❌ Neo4j: ${RED}STOPPED${NC}"
    fi
    
    echo ""
    echo "Port Forwarding Status:"
    echo "----------------------"
    
    # Check active port forwards
    if pgrep -f "kubectl port-forward.*keycloak.*8080" > /dev/null; then
        echo -e "✅ Keycloak port forward: ${GREEN}ACTIVE${NC}"
    else
        echo -e "❌ Keycloak port forward: ${RED}INACTIVE${NC}"
    fi
    
    if pgrep -f "kubectl port-forward.*mongodb.*27017" > /dev/null; then
        echo -e "✅ MongoDB port forward: ${GREEN}ACTIVE${NC}"
    else
        echo -e "❌ MongoDB port forward: ${RED}INACTIVE${NC}"
    fi
    
    if pgrep -f "kubectl port-forward.*mongo-express.*8081" > /dev/null; then
        echo -e "✅ Mongo Express port forward: ${GREEN}ACTIVE${NC}"
    else
        echo -e "❌ Mongo Express port forward: ${RED}INACTIVE${NC}"
    fi
    
    if pgrep -f "kubectl port-forward.*neo4j.*7474" > /dev/null; then
        echo -e "✅ Neo4j port forward: ${GREEN}ACTIVE${NC}"
    else
        echo -e "❌ Neo4j port forward: ${RED}INACTIVE${NC}"
    fi
}

# Test all services
test_all() {
    log_header "Testing All Services"
    
    echo "Testing MongoDB..."
    if [[ -f "$UTILS_DIR/test-mongodb-simple.py" ]]; then
        python3 "$UTILS_DIR/test-mongodb-simple.py" || log_warn "MongoDB test failed"
    else
        log_warn "MongoDB test script not found"
    fi
    
    echo ""
    echo "Testing Neo4j..."
    if [[ -f "$UTILS_DIR/test-neo4j-simple.py" ]]; then
        python3 "$UTILS_DIR/test-neo4j-simple.py" || log_warn "Neo4j test failed"
    else
        log_warn "Neo4j test script not found"
    fi
    
    log_success "Testing completed!"
}

# Cleanup databases only
cleanup_databases() {
    log_header "Cleaning Up Database Services"
    
    log_info "Cleaning up Neo4j..."
    bash "$DEPLOY_DIR/platform-neo4j.sh" --cleanup || log_warn "Neo4j cleanup failed"
    
    log_info "Cleaning up MongoDB..."
    bash "$DEPLOY_DIR/platform-mongodb.sh" --cleanup || log_warn "MongoDB cleanup failed"
    
    log_success "Database cleanup completed!"
}

# Cleanup everything
cleanup_all() {
    log_header "Cleaning Up Complete Platform"
    
    read -p "This will destroy ALL platform services. Are you sure? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleanup cancelled"
        exit 0
    fi
    
    cleanup_databases
    
    log_info "Cleaning up Keycloak..."
    bash "$DEPLOY_DIR/platform-keycloak.sh" --cleanup || log_warn "Keycloak cleanup failed"
    
    log_warn "Core infrastructure (Vault, External Secrets, Linkerd) requires manual cleanup"
    
    log_success "Platform cleanup completed!"
}

# Main execution
main() {
    local command="${1:-help}"
    
    case "$command" in
        "deploy-all")
            check_scripts
            deploy_all
            ;;
        "deploy-core")
            check_scripts
            deploy_core
            ;;
        "deploy-databases")
            check_scripts
            deploy_databases
            ;;
        "status")
            show_status
            ;;
        "test-all")
            check_scripts
            test_all
            ;;
        "cleanup-databases")
            check_scripts
            cleanup_databases
            ;;
        "cleanup-all")
            check_scripts
            cleanup_all
            ;;
        "help"|"--help"|"-h")
            usage
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
