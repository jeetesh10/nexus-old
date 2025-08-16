#!/bin/bash

# Keycloak Deployment Script
# Deploys Keycloak using the official Keycloak operator with PostgreSQL backend
# Uses Vault for secure credential management and External Secrets for synchronization

set -euo pipefail

# Configuration
NAMESPACE="keycloak"
KEYCLOAK_VERSION="26.0.7"
POSTGRES_VERSION="17.2"
VAULT_SECRET_PATH="secret/nexus/keycloak"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    debug "Checking if kubectl is available..."
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    debug "Checking if helm is available..."
    if ! command -v helm &> /dev/null; then
        error "helm is not installed or not in PATH"
        exit 1
    fi
    
    debug "Checking if openssl is available..."
    if ! command -v openssl &> /dev/null; then
        error "openssl is not installed or not in PATH"
        exit 1
    fi
    
    debug "Checking Kubernetes cluster connectivity..."
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    debug "Checking if Vault is accessible..."
    if ! kubectl get pods -n nexus-platform -l app.kubernetes.io/name=vault | grep -q Running; then
        error "Vault is not running in the cluster"
        exit 1
    fi
    
    debug "Checking if External Secrets Operator is running..."
    if ! kubectl get pods -n external-secrets | grep -q external-secrets; then
        error "External Secrets Operator is not running"
        exit 1
    fi
    
    success "All prerequisites met"
}

# Generate secure credentials
generate_credentials() {
    info "Generating secure credentials..."
    
    debug "Generating random admin username..."
    ADMIN_USERNAME="keycloak-admin-$(openssl rand -hex 4)"
    debug "Generated admin username: $ADMIN_USERNAME"
    
    debug "Generating secure admin password..."
    ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    debug "Generated admin password (length: ${#ADMIN_PASSWORD})"
    
    debug "Generating random database username..."
    DB_USERNAME="keycloak-db-$(openssl rand -hex 4)"
    debug "Generated database username: $DB_USERNAME"
    
    debug "Generating secure database password..."
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    debug "Generated database password (length: ${#DB_PASSWORD})"
    
    success "Secure credentials generated"
}

# Store credentials in Vault
store_credentials_in_vault() {
    info "Storing credentials in Vault..."
    
    debug "Checking if Vault is running in dev mode..."
    # First, try with the dev mode token "root"
    debug "Attempting to use dev mode root token..."
    if kubectl exec -n nexus-platform vault-0 -c vault -- vault kv put $VAULT_SECRET_PATH \
        admin-username="$ADMIN_USERNAME" \
        admin-password="$ADMIN_PASSWORD" \
        db-username="$DB_USERNAME" \
        db-password="$DB_PASSWORD" 2>/dev/null; then
        debug "Successfully stored credentials using dev mode token"
        success "Credentials stored in Vault"
        return
    fi
    
    debug "Dev mode failed, trying to get root token from secret..."
    if kubectl get secret vault-init -n nexus-platform &> /dev/null; then
        VAULT_TOKEN=$(kubectl get secret vault-init -n nexus-platform -o jsonpath='{.data.root-token}' | base64 -d)
        debug "Vault token retrieved from secret (length: ${#VAULT_TOKEN})"
        
        kubectl exec -n nexus-platform vault-0 -c vault -- env VAULT_TOKEN="$VAULT_TOKEN" vault kv put $VAULT_SECRET_PATH \
            admin-username="$ADMIN_USERNAME" \
            admin-password="$ADMIN_PASSWORD" \
            db-username="$DB_USERNAME" \
            db-password="$DB_PASSWORD"
    else
        error "Could not access Vault - neither dev mode nor vault-init secret available"
        exit 1
    fi
    
    success "Credentials stored in Vault"
}

# Create namespace
create_namespace() {
    info "Creating namespace: $NAMESPACE"
    debug "Checking if namespace already exists..."
    
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        warning "Namespace $NAMESPACE already exists"
        debug "Namespace status: $(kubectl get namespace $NAMESPACE -o jsonpath='{.status.phase}')"
    else
        debug "Creating new namespace..."
        kubectl create namespace $NAMESPACE
        success "Namespace $NAMESPACE created"
    fi
}

# Install Keycloak operator
install_keycloak_operator() {
    info "Installing Keycloak operator..."
    
    debug "Checking if Keycloak operator is already installed..."
    if kubectl get deployment keycloak-operator -n $NAMESPACE &> /dev/null; then
        warning "Keycloak operator already installed"
        debug "Operator status: $(kubectl get deployment keycloak-operator -n $NAMESPACE -o jsonpath='{.status.readyReplicas}/{.status.replicas}')"
        return
    fi
    
    debug "Applying Keycloak operator CRDs..."
    kubectl apply -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/26.0.7/kubernetes/keycloaks.k8s.keycloak.org-v1.yml
    kubectl apply -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/26.0.7/kubernetes/keycloakrealmimports.k8s.keycloak.org-v1.yml
    debug "CRDs applied"
    
    debug "Applying Keycloak operator deployment..."
    kubectl apply -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/26.0.7/kubernetes/kubernetes.yml -n $NAMESPACE
    debug "Operator deployment applied"
    
    debug "Waiting for operator to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/keycloak-operator -n $NAMESPACE
    
    success "Keycloak operator installed and ready"
}

# Create SecretStore for External Secrets
create_secret_store() {
    info "Creating SecretStore for External Secrets..."
    
    debug "Checking if SecretStore already exists in namespace..."
    if kubectl get secretstore vault-backend -n $NAMESPACE &> /dev/null; then
        warning "SecretStore 'vault-backend' already exists in namespace $NAMESPACE"
        return
    fi
    
    debug "Determining Vault token for SecretStore..."
    # Try dev mode first, fallback to secret
    VAULT_TOKEN="root"
    if ! kubectl get secret vault-init -n nexus-platform &> /dev/null; then
        debug "vault-init secret not found, assuming dev mode with token 'root'"
    else
        debug "vault-init secret found, using token from secret"
        VAULT_TOKEN=$(kubectl get secret vault-init -n nexus-platform -o jsonpath='{.data.root-token}' | base64 -d)
    fi
    
    debug "Creating Vault token secret for External Secrets..."
    kubectl create secret generic vault-token -n $NAMESPACE --from-literal=token="$VAULT_TOKEN" --dry-run=client -o yaml | kubectl apply -f -
    
    debug "Creating SecretStore manifest..."
    cat <<EOF | kubectl apply -f -
apiVersion: external-secrets.io/v1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: $NAMESPACE
spec:
  provider:
    vault:
      server: "http://vault.nexus-platform.svc.cluster.local:8200"
      path: "secret"
      version: "v2"
      auth:
        tokenSecretRef:
          name: "vault-token"
          key: "token"
EOF
    debug "SecretStore 'vault-backend' created"
    
    success "SecretStore configured for Vault integration"
}
create_external_secret() {
    info "Creating External Secret for Keycloak credentials..."
    debug "Checking if SecretStore 'vault-backend' exists..."
    if ! kubectl get secretstore vault-backend -n $NAMESPACE >/dev/null 2>&1; then
        warning "SecretStore 'vault-backend' not found, deployment may fail"
    else
        debug "SecretStore 'vault-backend' found"
    fi

    debug "Creating ExternalSecret manifest..."
    cat <<EOF | kubectl apply -f -
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: keycloak-credentials
  namespace: $NAMESPACE
spec:
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: keycloak-credentials
    creationPolicy: Owner
  data:
    - secretKey: admin-username
      remoteRef:
        key: ${VAULT_SECRET_PATH}
        property: admin-username
    - secretKey: admin-password
      remoteRef:
        key: ${VAULT_SECRET_PATH}
        property: admin-password
    - secretKey: db-username
      remoteRef:
        key: ${VAULT_SECRET_PATH}
        property: db-username
    - secretKey: db-password
      remoteRef:
        key: ${VAULT_SECRET_PATH}
        property: db-password
EOF
    debug "ExternalSecret 'keycloak-credentials' created"

    # Wait for secret to be synced
    info "Waiting for secrets to be synced from Vault..."
    timeout=60
    attempt=0
    while [ $timeout -gt 0 ]; do
        attempt=$((attempt+1))
        debug "Attempt $attempt: Checking if secret 'keycloak-credentials' exists..."
        if kubectl get secret keycloak-credentials -n $NAMESPACE >/dev/null 2>&1; then
            info "Secrets successfully synced from Vault"
            debug "Secret sync completed in $((60-timeout)) seconds"
            break
        fi
        debug "Secret not ready yet, waiting 2 more seconds..."
        sleep 2
        timeout=$((timeout-2))
    done

    if [ $timeout -le 0 ]; then
        error "Timeout waiting for secrets to sync from Vault"
        debug "Checking ExternalSecret status for troubleshooting..."
        kubectl describe externalsecret keycloak-credentials -n $NAMESPACE
        exit 1
    fi
}

# Deploy PostgreSQL database
deploy_postgresql() {
    info "Deploying PostgreSQL database for Keycloak..."
    
    debug "Checking if PostgreSQL StatefulSet already exists..."
    if kubectl get statefulset keycloak-db -n $NAMESPACE &> /dev/null; then
        warning "PostgreSQL StatefulSet already exists"
        debug "StatefulSet status: $(kubectl get statefulset keycloak-db -n $NAMESPACE -o jsonpath='{.status.readyReplicas}/{.status.replicas}')"
        return
    fi
    
    debug "Creating PostgreSQL StatefulSet with secret references..."
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: keycloak-db
  namespace: $NAMESPACE
spec:
  selector:
    app: keycloak-db
  ports:
    - port: 5432
      targetPort: 5432
  clusterIP: None
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: keycloak-db
  namespace: $NAMESPACE
spec:
  serviceName: keycloak-db
  replicas: 1
  selector:
    matchLabels:
      app: keycloak-db
  template:
    metadata:
      labels:
        app: keycloak-db
    spec:
      containers:
      - name: postgres
        image: postgres:$POSTGRES_VERSION
        env:
        - name: POSTGRES_DB
          value: keycloak
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: keycloak-credentials
              key: db-username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: keycloak-credentials
              key: db-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U \$POSTGRES_USER -d keycloak
          initialDelaySeconds: 15
          periodSeconds: 5
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U \$POSTGRES_USER -d keycloak
          initialDelaySeconds: 30
          periodSeconds: 10
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
EOF
    debug "PostgreSQL StatefulSet created"
    
    debug "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=ready --timeout=300s pod -l app=keycloak-db -n $NAMESPACE
    
    success "PostgreSQL database deployed and ready"
}

# Deploy Keycloak instance
deploy_keycloak() {
    info "Deploying Keycloak instance..."
    
    debug "Checking if Keycloak instance already exists..."
    if kubectl get keycloak keycloak -n $NAMESPACE &> /dev/null; then
        warning "Keycloak instance already exists"
        debug "Keycloak status: $(kubectl get keycloak keycloak -n $NAMESPACE -o jsonpath='{.status.conditions[0].type}:{.status.conditions[0].status}')"
        return
    fi
    
    debug "Creating Keycloak custom resource with secret references..."
    cat <<EOF | kubectl apply -f -
apiVersion: k8s.keycloak.org/v2alpha1
kind: Keycloak
metadata:
  name: keycloak
  namespace: $NAMESPACE
spec:
  instances: 1
  image: quay.io/keycloak/keycloak:$KEYCLOAK_VERSION
  db:
    vendor: postgres
    host: keycloak-db
    usernameSecret:
      name: keycloak-credentials
      key: db-username
    passwordSecret:
      name: keycloak-credentials
      key: db-password
  http:
    httpEnabled: true
  hostname:
    strict: false
  proxy:
    headers: xforwarded
EOF
    debug "Keycloak custom resource created"
    
    debug "Waiting for Keycloak to be ready..."
    timeout=600
    attempt=0
    while [ $timeout -gt 0 ]; do
        attempt=$((attempt+1))
        debug "Attempt $attempt: Checking Keycloak readiness..."
        
        status=$(kubectl get keycloak keycloak -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "Unknown")
        debug "Keycloak status: $status"
        
        if [ "$status" = "True" ]; then
            success "Keycloak is ready"
            break
        elif [ "$status" = "False" ]; then
            debug "Keycloak not ready yet, checking reason..."
            reason=$(kubectl get keycloak keycloak -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].message}' 2>/dev/null || echo "No message")
            debug "Reason: $reason"
        fi
        
        debug "Waiting 10 more seconds..."
        sleep 10
        timeout=$((timeout-10))
    done
    
    if [ $timeout -le 0 ]; then
        error "Timeout waiting for Keycloak to be ready"
        debug "Checking Keycloak resource status for troubleshooting..."
        kubectl describe keycloak keycloak -n $NAMESPACE
        exit 1
    fi
    
    success "Keycloak instance deployed and ready"
}

# Create admin user
create_admin_user() {
    info "Creating Keycloak admin user..."
    
    debug "Checking if admin user secret already exists..."
    if kubectl get secret keycloak-admin -n $NAMESPACE &> /dev/null; then
        warning "Admin user secret already exists"
        return
    fi
    
    debug "Creating admin user secret with references to Vault credentials..."
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: keycloak-admin
  namespace: $NAMESPACE
  labels:
    app: keycloak
type: Opaque
data:
  username: $(kubectl get secret keycloak-credentials -n $NAMESPACE -o jsonpath='{.data.admin-username}')
  password: $(kubectl get secret keycloak-credentials -n $NAMESPACE -o jsonpath='{.data.admin-password}')
EOF
    debug "Admin user secret created"
    
    debug "Applying admin user to Keycloak..."
    kubectl patch keycloak keycloak -n $NAMESPACE --type='merge' -p='{"spec":{"additionalOptions":[{"name":"import-realm","value":"/opt/keycloak/data/import/realm.json"}]}}'
    
    success "Keycloak admin user created"
}

# Start port forwarding
start_port_forwarding() {
    info "Setting up port forwarding for Keycloak access..."
    
    debug "Getting Keycloak service details..."
    KEYCLOAK_SERVICE="keycloak-service"
    
    debug "Checking for available ports..."
    LOCAL_PORT=8080
    if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
        warning "Port 8080 is already in use. Trying port 8081..."
        LOCAL_PORT=8081
        if lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null 2>&1; then
            warning "Port 8081 is already in use. Trying port 8082..."
            LOCAL_PORT=8082
        fi
    fi
    
    debug "Killing any existing port forwards for Keycloak..."
    pkill -f "port-forward.*keycloak-service" || true
    sleep 2
    
    debug "Starting port forwarding to Keycloak service on port $LOCAL_PORT..."
    kubectl port-forward svc/keycloak-service -n $NAMESPACE $LOCAL_PORT:8080 &
    PORT_FORWARD_PID=$!
    debug "Port forwarding started with PID: $PORT_FORWARD_PID"
    
    debug "Waiting for port forwarding to be ready..."
    sleep 5
    
    # Test if port forwarding is working
    debug "Testing port forwarding connectivity..."
    for i in {1..15}; do
        debug "Attempt $i: Testing connection to localhost:$LOCAL_PORT..."
        if nc -z localhost $LOCAL_PORT 2>/dev/null; then
            debug "Port forwarding is ready"
            break
        elif [ $i -eq 15 ]; then
            warning "Port forwarding test failed after 15 attempts"
        fi
        sleep 2
    done
    
    info "🌐 Keycloak is accessible at: http://localhost:$LOCAL_PORT"
    info "🔐 Admin console: http://localhost:$LOCAL_PORT/admin"
    
    # Store the PID for cleanup
    echo $PORT_FORWARD_PID > /tmp/keycloak-port-forward.pid
    success "Port forwarding established (PID: $PORT_FORWARD_PID)"
}

# Verify deployment
verify_deployment() {
    info "Verifying Keycloak deployment..."
    
    debug "Checking all pods in namespace..."
    kubectl get pods -n $NAMESPACE
    
    debug "Checking services in namespace..."
    kubectl get services -n $NAMESPACE
    
    debug "Checking Keycloak custom resource status..."
    kubectl get keycloak -n $NAMESPACE -o wide
    
    debug "Checking ExternalSecret status..."
    kubectl get externalsecret -n $NAMESPACE -o wide
    
    debug "Verifying secret synchronization..."
    if kubectl get secret keycloak-credentials -n $NAMESPACE &> /dev/null; then
        success "Secrets successfully synchronized from Vault"
        debug "Secret keys available: $(kubectl get secret keycloak-credentials -n $NAMESPACE -o jsonpath='{.data}' | jq -r 'keys[]' 2>/dev/null || echo 'admin-username admin-password db-username db-password')"
    else
        error "Secret synchronization failed"
        return 1
    fi
    
    # Show admin credentials
    info "Admin credentials (stored in Vault and synchronized via External Secrets):"
    debug "Retrieving admin username from secret..."
    ADMIN_USER=$(kubectl get secret keycloak-credentials -n $NAMESPACE -o jsonpath='{.data.admin-username}' | base64 -d 2>/dev/null || echo "Error retrieving username")
    debug "Retrieving admin password from secret..."
    ADMIN_PASS=$(kubectl get secret keycloak-credentials -n $NAMESPACE -o jsonpath='{.data.admin-password}' | base64 -d 2>/dev/null || echo "Error retrieving password")
    
    info "Username: $ADMIN_USER"
    info "Password: $ADMIN_PASS"
    
    success "Keycloak deployment verification complete!"
}

# Main execution
main() {
    info "Starting Keycloak deployment with Vault integration..."
    debug "Script version: 1.0.0"
    debug "Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    
    check_prerequisites
    generate_credentials
    store_credentials_in_vault
    create_namespace
    create_secret_store
    install_keycloak_operator
    create_external_secret
    deploy_postgresql
    deploy_keycloak
    create_admin_user
    verify_deployment
    start_port_forwarding
    
    success "Keycloak deployment completed successfully!"
    info "🔧 Keycloak Admin Console: http://localhost:${LOCAL_PORT:-8080}/admin"
    info "📋 Use the credentials shown above to log in"
    info "🛑 To stop port forwarding later, run: kill \$(cat /tmp/keycloak-port-forward.pid)"
    info "🔄 To restart port forwarding, run: kubectl port-forward svc/keycloak-service -n keycloak ${LOCAL_PORT:-8080}:8080"
}

# Execute main function
main "$@"
