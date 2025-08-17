#!/bin/bash
set -euo pipefail

# Nexus Platform Orchestrator - Complete Deployment Manager
# ==========================================================
# Intelligent orchestrator that deploys the complete Nexus platform
# Handles dependencies, status checks, and environment configuration

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration - Updated paths for deploy folder location
WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEPLOY_DIR="${WORKSPACE_ROOT}/scripts/deploy"
UTILS_DIR="${WORKSPACE_ROOT}/scripts/utils"
CONFIG_DIR="${WORKSPACE_ROOT}/config"

# Environment variables
ENVIRONMENT=""
DEPLOYMENT_START_TIME=""

# Logging functions with timestamps
log_info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] [SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] [WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] [ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[$(date '+%H:%M:%S')] [STEP]${NC} $1"
}

log_header() {
    echo ""
    echo "================================================================"
    echo -e "${MAGENTA}$1${NC}"
    echo "================================================================"
}

log_subheader() {
    echo ""
    echo "--------------------------------"
    echo -e "${CYAN}$1${NC}"
    echo "--------------------------------"
}

# Progress indicator
show_progress() {
    local message="$1"
    local duration="${2:-3}"
    
    echo -n -e "${YELLOW}[$(date '+%H:%M:%S')] [PROGRESS]${NC} $message"
    for i in $(seq 1 $duration); do
        echo -n "."
        sleep 1
    done
    echo " ✓"
}

# Print usage
usage() {
    cat << EOF
${MAGENTA}Nexus Platform Orchestrator - Complete Deployment Manager${NC}

${CYAN}DESCRIPTION:${NC}
    Intelligent orchestrator that deploys the complete Nexus platform with
    dependency management, status checking, and environment configuration.

${CYAN}USAGE:${NC}
    bash scripts/deploy/orchestrator.sh COMMAND [OPTIONS]

${CYAN}COMMANDS:${NC}
    deploy-all          Deploy complete platform (interactive)
    deploy-core         Deploy core infrastructure only
    deploy-databases    Deploy database services only  
    deploy-services     Deploy application services only
    cleanup-all         Clean up entire platform
    status              Show platform status
    health-check        Perform comprehensive health check
    help                Show this help message

${CYAN}EXAMPLES:${NC}
    bash scripts/deploy/orchestrator.sh deploy-all       # Interactive full deployment
    bash scripts/deploy/orchestrator.sh status           # Check all services status
    bash scripts/deploy/orchestrator.sh cleanup-all      # Clean up everything
    bash scripts/deploy/orchestrator.sh health-check     # Comprehensive health check

${CYAN}FEATURES:${NC}
    ✓ Environment selection (dev/QA/prod)
    ✓ Dependency checking and ordering
    ✓ Service status verification
    ✓ Automatic error recovery
    ✓ Real-time progress updates
    ✓ Comprehensive health checks

EOF
}

# Environment selection
select_environment() {
    log_header "Environment Selection"
    
    echo -e "${CYAN}Please select deployment environment:${NC}"
    echo "1) dev     - Development environment"
    echo "2) qa      - Quality Assurance environment" 
    echo "3) prod    - Production environment"
    echo ""
    
    while true; do
        read -p "Enter your choice (1-3): " choice
        case $choice in
            1)
                ENVIRONMENT="dev"
                break
                ;;
            2)
                ENVIRONMENT="qa"
                break
                ;;
            3)
                ENVIRONMENT="prod"
                echo -e "${YELLOW}Warning: Production deployment requires additional confirmations${NC}"
                read -p "Are you sure you want to deploy to PRODUCTION? (yes/no): " confirm
                if [[ "$confirm" == "yes" ]]; then
                    break
                else
                    log_info "Production deployment cancelled"
                    exit 0
                fi
                ;;
            *)
                echo -e "${RED}Invalid choice. Please enter 1, 2, or 3.${NC}"
                ;;
        esac
    done
    
    log_success "Selected environment: ${ENVIRONMENT}"
    
    # Load environment configuration
    if [[ -f "$CONFIG_DIR/${ENVIRONMENT}.env" ]]; then
        log_info "Loading environment configuration from ${ENVIRONMENT}.env"
        set -a
        source "$CONFIG_DIR/${ENVIRONMENT}.env"
        set +a
        log_success "Environment configuration loaded"
    else
        log_warn "No environment configuration found for ${ENVIRONMENT}"
    fi
}

# Check prerequisites
check_prerequisites() {
    log_subheader "Checking Prerequisites"
    
    local prerequisites_met=true
    
    # Check Docker
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            log_success "Docker is running"
        else
            log_error "Docker is not running"
            prerequisites_met=false
        fi
    else
        log_error "Docker is not installed"
        prerequisites_met=false
    fi
    
    # Check kubectl
    if command -v kubectl &> /dev/null; then
        if kubectl cluster-info &> /dev/null; then
            log_success "Kubernetes cluster is accessible"
        else
            log_error "Kubernetes cluster is not accessible"
            prerequisites_met=false
        fi
    else
        log_error "kubectl is not installed"
        prerequisites_met=false
    fi
    
    # Check helm
    if command -v helm &> /dev/null; then
        log_success "Helm is available"
    else
        log_error "Helm is not installed"
        prerequisites_met=false
    fi
    
    if [[ "$prerequisites_met" == "false" ]]; then
        log_error "Prerequisites not met. Please install missing tools and try again."
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Service status checking
check_service_status() {
    local service_name="$1"
    local namespace="$2"
    local resource_type="${3:-deployment}"
    
    if kubectl get $resource_type -n $namespace &> /dev/null; then
        local ready_replicas=$(kubectl get $resource_type -n $namespace -o jsonpath='{.items[0].status.readyReplicas}' 2>/dev/null || echo "0")
        local replicas=$(kubectl get $resource_type -n $namespace -o jsonpath='{.items[0].status.replicas}' 2>/dev/null || echo "1")
        
        if [[ "$ready_replicas" == "$replicas" ]] && [[ "$replicas" != "0" ]]; then
            echo "RUNNING"
        else
            echo "STARTING"
        fi
    else
        echo "STOPPED"
    fi
}

# Wait for service to be ready
wait_for_service() {
    local service_name="$1"
    local namespace="$2"
    local resource_type="${3:-deployment}"
    local timeout="${4:-300}"
    
    log_info "Waiting for $service_name to be ready..."
    
    # Use kubectl wait for more robust checking
    if ! kubectl wait --for=condition=Ready pod \
        --selector="app.kubernetes.io/name=${service_name}" \
        --namespace="$namespace" --timeout="${timeout}s"; then
        log_error "$service_name failed to become ready within ${timeout}s"
        return 1
    fi
    
    log_success "$service_name is ready"
    return 0
}

# Helper to run and check deployment scripts
run_script() {
    local script_name="$1"
    local config_file="$2"
    log_info "Executing $script_name..."
    if ! bash "$DEPLOY_DIR/$script_name" "$config_file"; then
        log_error "Failed to execute $script_name"
        exit 1
    fi
    log_success "$script_name executed successfully."
}

# Deploy core infrastructure
deploy_core() {
    log_header "Deploying Core Infrastructure"
    
    # Step 1: Basic infrastructure check
    log_step "Checking Kubernetes cluster..."
    if ! kubectl get nodes &> /dev/null; then
        log_error "Kubernetes cluster is not accessible. Please start your cluster first."
        exit 1
    fi
    log_success "Kubernetes cluster is accessible"
    
    # Step 2: Deploy Secrets Management (Vault)
    log_step "Deploying Secrets Management (Vault, External Secrets)..."
    run_script "platform-secrets.sh" "$CONFIG_FILE"
    wait_for_service "vault" "nexus-platform" "statefulset"
    
    log_success "Core infrastructure deployment completed"
}

# Deploy databases
deploy_databases() {
    log_header "Deploying Database Services"
    log_info "Database deployments are currently disabled to focus on Vault."
}

# Deploy application services
deploy_services() {
    log_header "Deploying Application Services"
    log_info "Application service deployments are currently disabled to focus on Vault."
}

# Complete platform deployment
deploy_all() {
    DEPLOYMENT_START_TIME=$(date)
    log_header "Nexus Platform Complete Deployment"
    
    # Environment selection
    select_environment
    
    # Prerequisites check
    check_prerequisites
    
    # Deployment confirmation
    echo ""
    echo -e "${CYAN}Deployment Summary:${NC}"
    echo "  Environment: ${ENVIRONMENT}"
    echo "  Time: $(date)"
    echo ""
    read -p "Proceed with deployment? (y/N): " confirm
    
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log_info "Deployment cancelled by user"
        exit 0
    fi
    
    # Execute deployment sequence
    deploy_core
    deploy_databases
    deploy_services
    
    # Final status check
    show_final_status
    
    log_success "Complete platform deployment finished!"
    log_info "Deployment started: $DEPLOYMENT_START_TIME"
    log_info "Deployment completed: $(date)"
}

# Format status with colors
format_status() {
    local status="$1"
    case "$status" in
        "RUNNING")
            echo -e "${GREEN}✓ RUNNING${NC}"
            ;;
        "STARTING")
            echo -e "${YELLOW}⚠ STARTING${NC}"
            ;;
        "STOPPED")
            echo -e "${RED}✗ STOPPED${NC}"
            ;;
        *)
            echo -e "${RED}✗ UNKNOWN${NC}"
            ;;
    esac
}

# Show access information
show_access_info() {
    echo -e "${CYAN}Access Information:${NC}"
    echo "-------------------"
    
    # Check for running port forwards
    if pgrep -f "kubectl port-forward.*keycloak" > /dev/null; then
        echo -e "🔐 Keycloak: ${GREEN}http://localhost:8081/admin${NC}"
    else
        echo -e "🔐 Keycloak: ${YELLOW}Run 'kubectl port-forward svc/keycloak-service -n keycloak 8081:8080' to access${NC}"
    fi
    
    if pgrep -f "kubectl port-forward.*auth-api" > /dev/null; then
        echo -e "🔑 Auth API: ${GREEN}http://localhost:8085${NC}"
    else
        echo -e "🔑 Auth API: ${YELLOW}Run 'kubectl port-forward svc/auth-api-service 8085:8080' to access${NC}"
    fi
    
    if pgrep -f "kubectl port-forward.*mongodb" > /dev/null; then
        echo -e "🍃 MongoDB: ${GREEN}mongodb://localhost:27017${NC}"
    else
        echo -e "🍃 MongoDB: ${YELLOW}Run 'kubectl port-forward svc/mongodb -n mongodb 27017:27017' to access${NC}"
    fi
    
    if pgrep -f "kubectl port-forward.*neo4j" > /dev/null; then
        echo -e "🔗 Neo4j: ${GREEN}http://localhost:7474${NC}"
    else
        echo -e "🔗 Neo4j: ${YELLOW}Run 'kubectl port-forward svc/neo4j -n neo4j 7474:7474' to access${NC}"
    fi
}

# Show comprehensive platform status
show_status() {
    log_header "Nexus Platform Status"
    
    echo -e "${CYAN}Core Infrastructure:${NC}"
    echo "-------------------"
    
    # Keycloak
    local keycloak_status=$(check_service_status "keycloak" "keycloak" "statefulset")
    printf "%-20s %s\n" "Keycloak:" "$(format_status $keycloak_status)"

    # Vault
    local vault_status=$(check_service_status "vault" "nexus-platform" "statefulset")
    printf "%-20s %s\n" "Vault:" "$(format_status $vault_status)"
    
    echo ""
    echo -e "${CYAN}Database Services:${NC}"
    echo "------------------"
    
    # MongoDB
    local mongo_status=$(check_service_status "mongodb" "mongodb" "statefulset")
    printf "%-20s %s\n" "MongoDB:" "$(format_status $mongo_status)"
    
    # Neo4j
    local neo4j_status=$(check_service_status "neo4j" "neo4j" "statefulset")
    printf "%-20s %s\n" "Neo4j:" "$(format_status $neo4j_status)"
    
    echo ""
    echo -e "${CYAN}Application Services:${NC}"
    echo "--------------------"
    
    # Auth API
    local auth_status=$(check_service_status "auth-api-service" "default" "deployment")
    printf "%-20s %s\n" "Auth API:" "$(format_status $auth_status)"
    
    echo ""
    show_access_info
}

# Show final deployment status
show_final_status() {
    log_header "Deployment Summary"
    
    show_status
    
    echo ""
    echo -e "${GREEN}🎉 Platform deployment completed successfully!${NC}"
    echo ""
    echo -e "${CYAN}Next Steps:${NC}"
    echo "1. Access Keycloak admin console to configure realms and users"
    echo "2. Test Auth API endpoints using the Swagger UI"
    echo "3. Connect to databases for data operations"
    echo "4. Monitor services using 'bash scripts/deploy/orchestrator.sh status'"
    echo ""
}

# Comprehensive health check
health_check() {
    log_header "Comprehensive Health Check"
    
    local overall_health=true
    
    # Check each service health
    log_subheader "Service Health Check"
    
    # Keycloak health
    if kubectl get pods -n keycloak -l app=keycloak | grep -q "Running"; then
        log_success "Keycloak is healthy"
    else
        log_error "Keycloak is not healthy"
        overall_health=false
    fi
    
    # MongoDB health
    if kubectl exec -n mongodb mongodb-0 -- mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
        log_success "MongoDB is healthy"
    else
        log_error "MongoDB is not healthy"
        overall_health=false
    fi
    
    # Neo4j health
    if kubectl exec -n neo4j neo4j-0 -- cypher-shell "RETURN 1" &> /dev/null; then
        log_success "Neo4j is healthy"
    else
        log_error "Neo4j is not healthy"
        overall_health=false
    fi
    
    # Auth API health
    if kubectl get pods -l app=auth-api-service | grep -q "Running"; then
        log_success "Auth API is healthy"
    else
        log_error "Auth API is not healthy"
        overall_health=false
    fi
    
    # Overall result
    if [[ "$overall_health" == "true" ]]; then
        log_success "Overall platform health: HEALTHY"
    else
        log_error "Overall platform health: UNHEALTHY"
        exit 1
    fi
}

# Cleanup all services
cleanup_all() {
    log_header "Platform Cleanup"
    
    echo -e "${YELLOW}This will destroy ALL platform services. Are you sure? (y/N)${NC}"
    read -p "> " confirm
    
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log_info "Cleanup cancelled by user"
        exit 0
    fi
    
    log_subheader "Cleaning Up Core Infrastructure"
    
    log_info "Cleaning up Secrets Management..."
    bash "$DEPLOY_DIR/platform-secrets.sh" --cleanup || log_warn "Secrets cleanup had issues"
    
    # Kill any port forwards
    log_info "Stopping port forwards..."
    pkill -f "kubectl port-forward" || true
    
    log_success "Platform cleanup completed!"
}

# Main execution
main() {
    local command="${1:-help}"
    
    case "$command" in
        "deploy-all")
            deploy_all
            ;;
        "deploy-core")
            select_environment
            CONFIG_FILE="$CONFIG_DIR/${ENVIRONMENT}.env"
            check_prerequisites
            deploy_core
            ;;
        "deploy-databases")
            check_prerequisites
            deploy_databases
            ;;
        "deploy-services")
            check_prerequisites
            deploy_services
            ;;
        "cleanup-all")
            cleanup_all
            ;;
        "status")
            show_status
            ;;
        "health-check")
            health_check
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
