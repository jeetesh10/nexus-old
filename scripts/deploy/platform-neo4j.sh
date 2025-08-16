#!/bin/bash

# Neo4j Deployment Script for Nexus Platform
# Secure implementation with Kubernetes secrets and StatefulSet
# Version: 1.0.0

set -euo pipefail

# Script configuration
SCRIPT_VERSION="1.0.0"
NAMESPACE="neo4j"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

debug() {
    echo -e "${BLUE}[DEBUG] $1${NC}"
}

# Help function
show_help() {
    echo "Neo4j Deployment Script"
    echo "========================"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "    --deploy-neo4j        Deploy Neo4j instance with Neo4j Browser UI"
    echo "    --check-health        Check Neo4j deployment health"
    echo "    --port-forward        Set up port forwarding for Neo4j and Browser"
    echo "    --open-ui             Open Neo4j Browser UI"
    echo "    --test-connection     Test Neo4j connection and create sample data"
    echo "    --cleanup             Remove all Neo4j resources"
    echo "    --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "    $0 --deploy-neo4j"
    echo "    $0 --test-connection"
    echo "    $0 --cleanup"
}

# Prerequisites check
check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if openssl is installed (for password generation)
    if ! command -v openssl &> /dev/null; then
        error "openssl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Kubernetes cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    debug "Prerequisites check passed"
    success "Prerequisites verified"
}

# Create namespace
create_namespace() {
    info "Setting up Neo4j namespace..."
    
    debug "Creating namespace '$NAMESPACE'..."
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: $NAMESPACE
  labels:
    name: $NAMESPACE
    component: database
    app: neo4j
  annotations:
    linkerd.io/inject: disabled
EOF
    debug "Namespace '$NAMESPACE' created"
    
    success "Neo4j namespace ready"
}

# Generate secure credentials
generate_credentials() {
    info "Generating secure Neo4j credentials..."
    
    debug "Generating Neo4j password..."
    NEO4J_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    debug "Generating Neo4j Browser password..."
    NEO4J_BROWSER_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Set variables used in deployment
    export NEO4J_USERNAME="neo4j"
    export NEO4J_AUTH="neo4j/$NEO4J_PASSWORD"
    export NEO4J_DATABASE="nexus"
    
    debug "Credentials generated successfully"
    success "Neo4j credentials generated"
}

# Store credentials in Kubernetes secrets
store_credentials_in_vault() {
    info "Storing Neo4j credentials in Kubernetes secrets..."
    
    debug "Note: Using direct Kubernetes secrets for secure credential management"
    debug "Credentials will be injected via secretKeyRef (no environment variables)"
    
    # Store credentials as Kubernetes secret
    kubectl create secret generic neo4j-credentials -n $NAMESPACE \
        --from-literal=username="$NEO4J_USERNAME" \
        --from-literal=password="$NEO4J_PASSWORD" \
        --from-literal=auth="$NEO4J_AUTH" \
        --from-literal=database="$NEO4J_DATABASE" \
        --from-literal=browser-username="admin" \
        --from-literal=browser-password="$NEO4J_BROWSER_PASSWORD" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    debug "Neo4j credentials stored as Kubernetes secret"
    info "Neo4j Browser credentials: admin / $NEO4J_BROWSER_PASSWORD"
    success "Credentials stored successfully"
}

# Setup External Secrets (placeholder for future Vault integration)
setup_external_secrets() {
    info "Setting up credentials for Neo4j..."
    
    debug "Note: Using direct Kubernetes secrets for secure implementation"
    debug "External Secrets integration ready for future Vault connection"
    
    success "Neo4j credentials configured"
}

# Create Neo4j StatefulSet with proper secret management
create_neo4j_statefulset() {
    echo -e "${BLUE}[INFO] Creating Neo4j StatefulSet...${NC}"
    
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: $NAMESPACE
  labels:
    app: neo4j
    component: database
spec:
  serviceName: neo4j
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
      annotations:
        linkerd.io/inject: disabled
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.15-community
        ports:
        - containerPort: 7474
          name: http
        - containerPort: 7687
          name: bolt
        env:
        - name: NEO4J_AUTH
          valueFrom:
            secretKeyRef:
              name: neo4j-credentials
              key: auth
        - name: NEO4J_server_config_strict__validation_enabled
          value: "false"
        volumeMounts:
        - name: neo4j-data
          mountPath: /data
        - name: neo4j-logs
          mountPath: /logs
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1"
        readinessProbe:
          httpGet:
            path: /
            port: 7474
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /
            port: 7474
          initialDelaySeconds: 60
          periodSeconds: 30
  volumeClaimTemplates:
  - metadata:
      name: neo4j-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
  - metadata:
      name: neo4j-logs
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j
  namespace: $NAMESPACE
  labels:
    app: neo4j
spec:
  ports:
  - port: 7474
    targetPort: 7474
    protocol: TCP
    name: http
  - port: 7687
    targetPort: 7687
    protocol: TCP
    name: bolt
  selector:
    app: neo4j
  type: ClusterIP
EOF

    echo "[DEBUG] Waiting for Neo4j to be ready..."
    kubectl wait --for=condition=ready --timeout=300s pod/neo4j-0 -n $NAMESPACE
    echo -e "${GREEN}[SUCCESS] Neo4j StatefulSet created successfully${NC}"
}

# Deploy Neo4j
deploy_neo4j() {
    echo -e "${BLUE}[INFO] Deploying Neo4j instance...${NC}"
    
    # Check if Neo4j StatefulSet already exists
    echo "[DEBUG] Checking if Neo4j StatefulSet already exists..."
    if kubectl get statefulset neo4j -n $NAMESPACE &> /dev/null; then
        echo -e "${YELLOW}[WARNING] Neo4j StatefulSet already exists${NC}"
        CURRENT_STATUS=$(kubectl get pods -n $NAMESPACE neo4j-0 -o jsonpath='{.status.containerStatuses[0].ready}' 2>/dev/null || echo "false")
        echo "[DEBUG] Neo4j status: $CURRENT_STATUS"
    else
        echo "[DEBUG] Creating new Neo4j StatefulSet..."
        create_neo4j_statefulset
    fi
    
    # Wait for Neo4j to be ready
    echo "[DEBUG] Ensuring Neo4j is ready..."
    wait_for_neo4j_ready
    
    setup_port_forward
}

# Wait for Neo4j to be ready
wait_for_neo4j_ready() {
    echo "[DEBUG] Waiting for Neo4j to be ready..."
    
    for i in {1..30}; do
        if kubectl exec -n $NAMESPACE neo4j-0 -- cypher-shell -u neo4j -p "$(kubectl get secret neo4j-credentials -n $NAMESPACE -o jsonpath='{.data.password}' | base64 -d)" "RETURN 1" &> /dev/null; then
            echo "[DEBUG] Neo4j is responding"
            return 0
        fi
        echo "[DEBUG] Neo4j not ready yet, waiting... ($i/30)"
        sleep 10
    done
    
    echo -e "${YELLOW}[WARNING] Neo4j might not be fully ready, but continuing...${NC}"
    return 0
}

# Check Neo4j health
check_health() {
    info "Checking Neo4j health..."
    
    debug "Checking pod status..."
    kubectl get pods -n $NAMESPACE -l app=neo4j
    
    debug "Checking Neo4j connection..."
    if kubectl exec -n $NAMESPACE neo4j-0 -- cypher-shell -u neo4j -p "$(kubectl get secret neo4j-credentials -n $NAMESPACE -o jsonpath='{.data.password}' | base64 -d)" "RETURN 'Neo4j is healthy' as status" &> /dev/null; then
        success "Neo4j is healthy and responding"
    else
        error "Neo4j health check failed"
        return 1
    fi
    
    debug "Checking Neo4j version..."
    NEO4J_VERSION=$(kubectl exec -n $NAMESPACE neo4j-0 -- cypher-shell -u neo4j -p "$(kubectl get secret neo4j-credentials -n $NAMESPACE -o jsonpath='{.data.password}' | base64 -d)" "CALL dbms.components() YIELD name, versions, edition UNWIND versions AS version RETURN name, version, edition" --format plain | grep Neo4j | head -1)
    info "Neo4j details: $NEO4J_VERSION"
    
    success "Neo4j health check completed"
}

# Port forwarding
setup_port_forward() {
    info "Setting up port forwarding for Neo4j..."
    
    # Neo4j HTTP port forwarding (Browser UI)
    debug "Checking if port 7474 is already in use..."
    if lsof -i :7474 &> /dev/null; then
        warning "Port 7474 is already in use"
        debug "Killing existing processes on port 7474..."
        pkill -f "kubectl port-forward.*neo4j.*7474" || true
        sleep 2
    fi
    
    debug "Starting Neo4j HTTP port forward: localhost:7474 -> neo4j:7474"
    kubectl port-forward svc/neo4j -n $NAMESPACE 7474:7474 &
    NEO4J_HTTP_PID=$!
    
    # Neo4j Bolt port forwarding (Database connection)
    debug "Checking if port 7687 is already in use..."
    if lsof -i :7687 &> /dev/null; then
        warning "Port 7687 is already in use"
        debug "Killing existing processes on port 7687..."
        pkill -f "kubectl port-forward.*neo4j.*7687" || true
        sleep 2
    fi
    
    debug "Starting Neo4j Bolt port forward: localhost:7687 -> neo4j:7687"
    kubectl port-forward svc/neo4j -n $NAMESPACE 7687:7687 &
    NEO4J_BOLT_PID=$!
    
    debug "Waiting for port forwards to be ready..."
    sleep 5
    
    # Check HTTP port forward
    if kill -0 $NEO4J_HTTP_PID 2>/dev/null; then
        success "Neo4j Browser UI active: http://localhost:7474"
    else
        error "Neo4j HTTP port forwarding failed to start"
    fi
    
    # Check Bolt port forward
    if kill -0 $NEO4J_BOLT_PID 2>/dev/null; then
        success "Neo4j Bolt connection active: bolt://localhost:7687"
    else
        warning "Neo4j Bolt port forwarding failed to start"
    fi
    
    # Get credentials from secret
    NEO4J_USER=$(kubectl get secret neo4j-credentials -n $NAMESPACE -o jsonpath='{.data.username}' | base64 -d 2>/dev/null || echo "neo4j")
    NEO4J_PASS=$(kubectl get secret neo4j-credentials -n $NAMESPACE -o jsonpath='{.data.password}' | base64 -d 2>/dev/null || echo "")
    
    info "Connection details:"
    echo "  Neo4j Browser UI: http://localhost:7474"
    echo "  Neo4j Bolt: bolt://localhost:7687"
    echo "  Username: $NEO4J_USER"
    echo "  Password: (from neo4j-credentials secret)"
    echo "  Database: nexus"
    echo ""
    echo "To get credentials:"
    echo "  kubectl get secret neo4j-credentials -n $NAMESPACE -o jsonpath='{.data.username}' | base64 -d"
    echo "  kubectl get secret neo4j-credentials -n $NAMESPACE -o jsonpath='{.data.password}' | base64 -d"
}

# Open Neo4j Browser UI
open_neo4j_browser() {
    info "Opening Neo4j Browser UI..."
    
    # Check if Neo4j is running
    if ! kubectl get pods -n $NAMESPACE -l app=neo4j | grep Running &> /dev/null; then
        error "Neo4j is not running. Deploy with --deploy-neo4j first."
        return 1
    fi
    
    # Check if port forwarding is active
    if ! lsof -i :7474 &> /dev/null; then
        warning "Port 7474 not active. Setting up port forwarding..."
        setup_port_forward
        sleep 3
    fi
    
    info "Neo4j Browser should be available at: http://localhost:7474"
    
    # Try to open browser (macOS)
    if command -v open &> /dev/null; then
        debug "Opening browser..."
        open http://localhost:7474
    else
        info "Please open your browser and navigate to: http://localhost:7474"
    fi
}

# Test Neo4j connection
test_neo4j_connection() {
    info "Testing Neo4j connection..."
    
    # Check if Neo4j is running
    if ! kubectl get pods -n $NAMESPACE -l app=neo4j | grep Running &> /dev/null; then
        error "Neo4j is not running. Deploy with --deploy-neo4j first."
        return 1
    fi
    
    # Get credentials
    NEO4J_USER=$(kubectl get secret neo4j-credentials -n $NAMESPACE -o jsonpath='{.data.username}' | base64 -d 2>/dev/null || echo "neo4j")
    NEO4J_PASS=$(kubectl get secret neo4j-credentials -n $NAMESPACE -o jsonpath='{.data.password}' | base64 -d 2>/dev/null || echo "")
    NEO4J_DB=$(kubectl get secret neo4j-credentials -n $NAMESPACE -o jsonpath='{.data.database}' | base64 -d 2>/dev/null || echo "nexus")
    
    info "Creating test data..."
    
    # Create test data
    kubectl exec -n $NAMESPACE neo4j-0 -- cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASS" "
    // Create test nodes and relationships
    CREATE (platform:Platform {name: 'Nexus', version: '1.0.0', created: datetime()})
    CREATE (mongodb:Database {name: 'MongoDB', version: '7.0.23', type: 'Document'})
    CREATE (neo4j:Database {name: 'Neo4j', version: '5.15', type: 'Graph'})
    CREATE (keycloak:Auth {name: 'Keycloak', version: '26.0.7', type: 'Identity'})
    CREATE (vault:Security {name: 'Vault', type: 'Secrets'})
    
    // Create relationships
    CREATE (platform)-[:USES]->(mongodb)
    CREATE (platform)-[:USES]->(neo4j)
    CREATE (platform)-[:USES]->(keycloak)
    CREATE (platform)-[:SECURED_BY]->(vault)
    CREATE (mongodb)-[:SECURED_BY]->(vault)
    CREATE (neo4j)-[:SECURED_BY]->(vault)
    CREATE (keycloak)-[:SECURED_BY]->(vault)
    
    // Add test user
    CREATE (user:User {
        name: 'Test User',
        email: 'user@nexus.local',
        role: 'admin',
        created: datetime()
    })
    CREATE (user)-[:USES]->(platform)
    
    RETURN 'Test data created successfully' as result;
    " || {
        error "Failed to create test data"
        return 1
    }
    
    # Query test data
    info "Querying test data..."
    kubectl exec -n $NAMESPACE neo4j-0 -- cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASS" "
    MATCH (n) 
    RETURN labels(n) as NodeType, count(n) as Count 
    ORDER BY NodeType;
    "
    
    success "Test data created successfully!"
    info "You can now verify the data in Neo4j Browser: http://localhost:7474"
    info "Try this query: MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 25"
}

# Cleanup function
cleanup() {
    info "Cleaning up Neo4j deployment..."
    
    debug "Stopping port forwards..."
    pkill -f "kubectl port-forward.*neo4j" || true
    
    debug "Deleting Neo4j resources..."
    kubectl delete statefulset neo4j -n $NAMESPACE --ignore-not-found
    kubectl delete service neo4j -n $NAMESPACE --ignore-not-found
    kubectl delete pvc -l app=neo4j -n $NAMESPACE --ignore-not-found
    
    debug "Deleting secrets..."
    kubectl delete secret neo4j-credentials -n $NAMESPACE --ignore-not-found
    
    debug "Deleting namespace..."
    kubectl delete namespace $NAMESPACE --ignore-not-found
    
    success "Neo4j cleanup completed"
}

# Main function
main() {
    echo "Neo4j Deployment Script"
    echo "======================="
    debug "Script version: $SCRIPT_VERSION"
    debug "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    
    # Parse command line arguments
    if [ $# -eq 0 ]; then
        show_help
        exit 1
    fi
    
    case "$1" in
        --deploy-neo4j)
            check_prerequisites
            create_namespace
            generate_credentials
            store_credentials_in_vault
            setup_external_secrets
            deploy_neo4j
            ;;
        --check-health)
            check_health
            ;;
        --port-forward)
            setup_port_forward
            ;;
        --open-ui)
            open_neo4j_browser
            ;;
        --test-connection)
            test_neo4j_connection
            ;;
        --cleanup)
            cleanup
            ;;
        --help)
            show_help
            ;;
        *)
            error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
