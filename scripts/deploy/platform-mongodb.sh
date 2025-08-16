#!/bin/bash

# MongoDB Deployment Script with Vault Integration
# Version: 1.0.0
# Description: Deploy MongoDB with secure credential management

set -euo pipefail

# Script metadata
SCRIPT_VERSION="1.0.0"
NAMESPACE="mongodb"
MONGODB_VERSION="7.0"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
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

# Help function
show_help() {
    echo "MongoDB Deployment Script with Vault Integration"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "    --deploy-mongodb      Deploy MongoDB instance with Mongo Express UI"
    echo "    --check-health        Check MongoDB health"
    echo "    --port-forward        Set up port forwarding (MongoDB and Mongo Express)"
    echo "    --open-ui            Open Mongo Express web UI in browser"
    echo "    --test-connection    Test MongoDB connection and create sample data"
    echo "    --cleanup            Remove MongoDB deployment"
    echo "    --help               Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "    $0 --deploy-mongodb"
    echo "    $0 --check-health"
    echo "    $0 --port-forward"
    echo "    $0 --open-ui"
    echo "    $0 --test-connection"
    echo ""
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
    if ! kubectl get pods -n nexus-platform -l app.kubernetes.io/name=vault &> /dev/null; then
        error "Vault is not running in nexus-platform namespace"
        exit 1
    fi
    
    debug "Checking if External Secrets Operator is running..."
    if ! kubectl get pods -n external-secrets-system -l app.kubernetes.io/name=external-secrets &> /dev/null; then
        warning "External Secrets Operator is not running"
        # Don't exit here, we'll handle this case
    fi
    
    success "Prerequisites check completed"
}

# Create namespace
create_namespace() {
    info "Creating MongoDB namespace..."
    
    debug "Checking if namespace '$NAMESPACE' exists..."
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        warning "Namespace '$NAMESPACE' already exists"
        return
    fi
    
    debug "Creating namespace '$NAMESPACE'..."
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: $NAMESPACE
  labels:
    name: $NAMESPACE
    component: database
    app: mongodb
  annotations:
    linkerd.io/inject: disabled
EOF
    debug "Namespace '$NAMESPACE' created"
    
    success "MongoDB namespace ready"
}

# Generate secure credentials
generate_credentials() {
    info "Generating secure MongoDB credentials..."
    
    debug "Generating MongoDB root password..."
    MONGODB_ROOT_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    debug "Generating MongoDB database password..."
    MONGODB_DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Set variables used in Mongo Express and user creation
    export MONGO_ROOT_USERNAME="admin"
    export MONGO_ROOT_PASSWORD="$MONGODB_ROOT_PASSWORD"
    export MONGO_ROOT_DATABASE="nexus"
    
    debug "Credentials generated successfully"
    success "MongoDB credentials generated"
}

# Store credentials in Vault
store_credentials_in_vault() {
    info "Storing MongoDB credentials in Vault..."
    
    debug "Note: Vault integration temporarily disabled for initial testing"
    debug "Credentials will be stored as Kubernetes secrets directly"
    
    # Generate UI credentials for Mongo Express
    MONGO_EXPRESS_USER="admin"
    MONGO_EXPRESS_PASS=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-12)
    
    # Build MongoDB connection URL for Mongo Express
    MONGO_CONNECTION_URL="mongodb://$MONGO_ROOT_USERNAME:$MONGODB_ROOT_PASSWORD@mongodb:27017/$MONGO_ROOT_DATABASE?authSource=admin"
    
    # Store credentials as direct Kubernetes secret for now
    kubectl create secret generic mongodb-credentials -n $NAMESPACE \
        --from-literal=root-username="$MONGO_ROOT_USERNAME" \
        --from-literal=root-password="$MONGODB_ROOT_PASSWORD" \
        --from-literal=db-username="nexus" \
        --from-literal=db-password="$MONGODB_DB_PASSWORD" \
        --from-literal=database="$MONGO_ROOT_DATABASE" \
        --from-literal=auth-database="admin" \
        --from-literal=connection-url="$MONGO_CONNECTION_URL" \
        --from-literal=ui-username="$MONGO_EXPRESS_USER" \
        --from-literal=ui-password="$MONGO_EXPRESS_PASS" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    debug "MongoDB credentials stored as Kubernetes secret"
    info "Mongo Express UI credentials: $MONGO_EXPRESS_USER / $MONGO_EXPRESS_PASS"
    success "Credentials stored successfully"
}

# Setup External Secrets
setup_external_secrets() {
    info "Setting up credentials for MongoDB..."
    
    debug "Note: Using direct Kubernetes secrets for initial testing"
    debug "External Secrets integration will be added after Vault is properly configured"
    
    success "MongoDB credentials configured"
}

# Deploy MongoDB
# Function to deploy MongoDB instance
deploy_mongodb() {
    echo -e "${BLUE}[INFO] Deploying MongoDB instance...${NC}"
    
    # Check if MongoDB StatefulSet already exists
    echo "[DEBUG] Checking if MongoDB StatefulSet already exists..."
    if kubectl get statefulset mongodb -n $NAMESPACE &> /dev/null; then
        echo -e "${YELLOW}[WARNING] MongoDB StatefulSet already exists${NC}"
        CURRENT_STATUS=$(kubectl get pods -n $NAMESPACE mongodb-0 -o jsonpath='{.status.containerStatuses[0].ready}' 2>/dev/null || echo "false")
        echo "[DEBUG] MongoDB status: $CURRENT_STATUS"
    else
        echo "[DEBUG] Creating new MongoDB StatefulSet..."
        create_mongodb_statefulset
    fi
    
    # Ensure MongoDB user is properly created
    echo "[DEBUG] Ensuring MongoDB admin user is properly configured..."
    wait_for_mongodb_ready
    
    # Create/update admin user with proper authentication
    echo "[DEBUG] Creating/updating MongoDB admin user..."
    kubectl exec -n $NAMESPACE mongodb-0 -- mongosh --eval "
    use admin;
    const username = '$MONGO_ROOT_USERNAME';
    const password = '$MONGODB_ROOT_PASSWORD';
    try {
      db.createUser({
        user: username,
        pwd: password,
        roles: ['root']
      });
      print('Admin user created successfully');
    } catch(e) {
      if (e.message.includes('already exists')) {
        print('User already exists, updating password...');
        db.updateUser(username, {
          pwd: password,
          roles: ['root']
        });
        print('Password updated successfully');
      } else {
        throw e;
      }
    }
    " || echo "[WARNING] User creation/update had issues, but continuing..."
    
    # Deploy Mongo Express for UI access
    deploy_mongo_express
    
    setup_port_forward
}

# Create MongoDB StatefulSet with proper secret management
create_mongodb_statefulset() {
    echo -e "${BLUE}[INFO] Creating MongoDB StatefulSet...${NC}"
    
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
  namespace: $NAMESPACE
  labels:
    app: mongodb
    component: database
spec:
  serviceName: mongodb
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
      annotations:
        linkerd.io/inject: disabled
    spec:
      containers:
      - name: mongodb
        image: mongo:7.0
        ports:
        - containerPort: 27017
          name: mongodb
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          valueFrom:
            secretKeyRef:
              name: mongodb-credentials
              key: root-username
        - name: MONGO_INITDB_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mongodb-credentials
              key: root-password
        - name: MONGO_INITDB_DATABASE
          valueFrom:
            secretKeyRef:
              name: mongodb-credentials
              key: database
        volumeMounts:
        - name: mongodb-storage
          mountPath: /data/db
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          exec:
            command:
            - mongosh
            - --eval
            - "db.adminCommand('ping')"
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          exec:
            command:
            - mongosh
            - --eval
            - "db.adminCommand('ping')"
          initialDelaySeconds: 30
          periodSeconds: 10
  volumeClaimTemplates:
  - metadata:
      name: mongodb-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 5Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb
  namespace: $NAMESPACE
  labels:
    app: mongodb
spec:
  ports:
  - port: 27017
    targetPort: 27017
    protocol: TCP
    name: mongodb
  selector:
    app: mongodb
  type: ClusterIP
EOF

    echo "[DEBUG] Waiting for MongoDB to be ready..."
    kubectl wait --for=condition=ready --timeout=180s pod/mongodb-0 -n $NAMESPACE
    echo -e "${GREEN}[SUCCESS] MongoDB StatefulSet created successfully${NC}"
}

# Function to deploy Mongo Express UI
deploy_mongo_express() {
    echo -e "${BLUE}[INFO] Deploying Mongo Express UI...${NC}"
    
    # Create Mongo Express deployment
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongo-express
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mongo-express
  template:
    metadata:
      labels:
        app: mongo-express
      annotations:
        linkerd.io/inject: disabled
    spec:
      containers:
      - name: mongo-express
        image: mongo-express:1.0.2
        ports:
        - containerPort: 8081
        env:
        - name: ME_CONFIG_MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: mongodb-credentials
              key: connection-url
        - name: ME_CONFIG_MONGODB_ENABLE_ADMIN
          value: "true"
        - name: ME_CONFIG_BASICAUTH_USERNAME
          valueFrom:
            secretKeyRef:
              name: mongodb-credentials
              key: ui-username
        - name: ME_CONFIG_BASICAUTH_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mongodb-credentials
              key: ui-password
        - name: ME_CONFIG_REQUEST_SIZE
          value: "100kb"
        - name: ME_CONFIG_SITE_BASEURL
          value: "/"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: mongo-express
  namespace: $NAMESPACE
spec:
  selector:
    app: mongo-express
  ports:
  - port: 8081
    targetPort: 8081
    protocol: TCP
    name: http
  type: ClusterIP
EOF

    echo "[DEBUG] Waiting for Mongo Express to be ready..."
    kubectl wait --for=condition=available --timeout=120s deployment/mongo-express -n $NAMESPACE || {
        echo -e "${YELLOW}[WARNING] Mongo Express deployment timeout, checking status...${NC}"
        kubectl get pods -n $NAMESPACE -l app=mongo-express
    }
    
    echo -e "${GREEN}[SUCCESS] Mongo Express deployed${NC}"
}

# Wait for MongoDB to be ready
wait_for_mongodb_ready() {
    echo "[DEBUG] Waiting for MongoDB to be ready..."
    
    for i in {1..30}; do
        if kubectl exec -n $NAMESPACE mongodb-0 -- mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
            echo "[DEBUG] MongoDB is responding"
            return 0
        fi
        echo "[DEBUG] MongoDB not ready yet, waiting... ($i/30)"
        sleep 2
    done
    
    echo -e "${YELLOW}[WARNING] MongoDB might not be fully ready, but continuing...${NC}"
    return 0
}

# Check MongoDB health
check_health() {
    info "Checking MongoDB health..."
    
    debug "Checking pod status..."
    kubectl get pods -n $NAMESPACE -l app=mongodb
    
    debug "Checking MongoDB connection..."
    if kubectl exec -n $NAMESPACE mongodb-0 -- mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
        success "MongoDB is healthy and responding"
    else
        error "MongoDB health check failed"
        return 1
    fi
    
    debug "Checking MongoDB version..."
    MONGO_VERSION=$(kubectl exec -n $NAMESPACE mongodb-0 -- mongosh --eval "db.version()" --quiet)
    info "MongoDB version: $MONGO_VERSION"
    
    success "MongoDB health check completed"
}

# Port forwarding
setup_port_forward() {
    info "Setting up port forwarding for MongoDB and Mongo Express..."
    
    # MongoDB port forwarding
    debug "Checking if port 27017 is already in use..."
    if lsof -i :27017 &> /dev/null; then
        warning "Port 27017 is already in use"
        debug "Killing existing processes on port 27017..."
        pkill -f "kubectl port-forward.*mongodb.*27017" || true
        sleep 2
    fi
    
    debug "Starting MongoDB port forward: localhost:27017 -> mongodb:27017"
    kubectl port-forward svc/mongodb -n $NAMESPACE 27017:27017 &
    MONGO_PORT_FORWARD_PID=$!
    
    # Mongo Express port forwarding
    debug "Checking if port 8081 is already in use..."
    if lsof -i :8081 &> /dev/null; then
        warning "Port 8081 is already in use"
        debug "Killing existing processes on port 8081..."
        pkill -f "kubectl port-forward.*mongo-express.*8081" || true
        sleep 2
    fi
    
    debug "Starting Mongo Express port forward: localhost:8081 -> mongo-express:8081"
    kubectl port-forward svc/mongo-express -n $NAMESPACE 8081:8081 &
    EXPRESS_PORT_FORWARD_PID=$!
    
    debug "Waiting for port forwards to be ready..."
    sleep 5
    
    # Check MongoDB port forward
    if kill -0 $MONGO_PORT_FORWARD_PID 2>/dev/null; then
        success "MongoDB port forwarding active: mongodb://localhost:27017"
    else
        error "MongoDB port forwarding failed to start"
    fi
    
    # Check Mongo Express port forward
    if kill -0 $EXPRESS_PORT_FORWARD_PID 2>/dev/null; then
        # Get UI credentials from secret
        UI_USER=$(kubectl get secret mongodb-credentials -n $NAMESPACE -o jsonpath='{.data.ui-username}' | base64 -d 2>/dev/null || echo "admin")
        UI_PASS=$(kubectl get secret mongodb-credentials -n $NAMESPACE -o jsonpath='{.data.ui-password}' | base64 -d 2>/dev/null || echo "admin")
        
        success "Mongo Express UI active: http://localhost:8081"
        info "  Login: $UI_USER / $UI_PASS"
    else
        warning "Mongo Express port forwarding failed to start"
    fi
    
    info "Connection details:"
    echo "  MongoDB Host: localhost"
    echo "  MongoDB Port: 27017"
    echo "  Username: admin (from mongodb-credentials secret)"
    echo "  Password: (from mongodb-credentials secret)"
    echo "  Database: nexus"
    echo "  Web UI: http://localhost:8081"
    echo ""
    echo "To get credentials:"
    echo "  kubectl get secret mongodb-credentials -n $NAMESPACE -o jsonpath='{.data.root-username}' | base64 -d"
    echo "  kubectl get secret mongodb-credentials -n $NAMESPACE -o jsonpath='{.data.root-password}' | base64 -d"
    echo "  kubectl get secret mongodb-credentials -n $NAMESPACE -o jsonpath='{.data.ui-username}' | base64 -d"
    echo "  kubectl get secret mongodb-credentials -n $NAMESPACE -o jsonpath='{.data.ui-password}' | base64 -d"
}

# Open Mongo Express UI
open_mongo_express_ui() {
    info "Opening Mongo Express UI..."
    
    # Check if Mongo Express is running
    if ! kubectl get pods -n $NAMESPACE -l app=mongo-express | grep Running &> /dev/null; then
        error "Mongo Express is not running. Deploy with --deploy-mongodb first."
        return 1
    fi
    
    # Setup port forwarding if not active
    if ! lsof -i :8081 &> /dev/null; then
        info "Setting up port forwarding for Mongo Express..."
        kubectl port-forward svc/mongo-express -n $NAMESPACE 8081:8081 &
        sleep 3
    fi
    
    info "Mongo Express UI: http://localhost:8081"
    info "Login: admin / admin"
    
    # Try to open in browser
    if command -v open &> /dev/null; then
        open "http://localhost:8081"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:8081"
    else
        info "Please open http://localhost:8081 in your browser"
    fi
}

# Test MongoDB connection
test_mongodb_connection() {
    info "Testing MongoDB connection..."
    
    # Check if MongoDB is running
    if ! kubectl get pods -n $NAMESPACE -l app=mongodb | grep Running &> /dev/null; then
        error "MongoDB is not running. Deploy with --deploy-mongodb first."
        return 1
    fi
    
    # Get credentials
    MONGO_USER=$(kubectl get secret mongodb-credentials -n $NAMESPACE -o jsonpath='{.data.root-username}' | base64 -d 2>/dev/null || echo "admin")
    MONGO_PASS=$(kubectl get secret mongodb-credentials -n $NAMESPACE -o jsonpath='{.data.root-password}' | base64 -d 2>/dev/null || echo "")
    MONGO_DB=$(kubectl get secret mongodb-credentials -n $NAMESPACE -o jsonpath='{.data.database}' | base64 -d 2>/dev/null || echo "nexus")
    
    info "Creating test data..."
    
    # Create test data
    kubectl exec -n $NAMESPACE mongodb-0 -- mongosh "mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/$MONGO_DB?authSource=admin" --eval "
    // Create test collection with sample data
    db.test_collection.insertMany([
        {
            name: 'MongoDB Connection Test',
            timestamp: new Date(),
            type: 'connectivity_test',
            status: 'successful',
            metadata: {
                script: 'platform-mongodb.sh',
                version: '1.0.0',
                deployment_date: new Date()
            }
        },
        {
            name: 'Sample User',
            email: 'user@nexus.local',
            role: 'admin',
            created_at: new Date(),
            active: true
        },
        {
            name: 'Sample Service',
            type: 'microservice',
            port: 8080,
            status: 'running',
            replicas: 3
        }
    ]);
    
    print('=== Test Results ===');
    print('Documents inserted:', db.test_collection.countDocuments({}));
    print('Collections:', db.getCollectionNames().join(', '));
    print('Sample document:', JSON.stringify(db.test_collection.findOne(), null, 2));
    " || {
        error "Failed to create test data"
        return 1
    }
    
    success "Test data created successfully!"
    info "You can now verify the data in Mongo Express UI: http://localhost:8081"
}

# Cleanup function
cleanup() {
    info "Cleaning up MongoDB deployment..."
    
    debug "Stopping port forwards..."
    pkill -f "kubectl port-forward.*mongodb" || true
    
    debug "Deleting MongoDB resources..."
    kubectl delete statefulset mongodb -n $NAMESPACE --ignore-not-found
    kubectl delete service mongodb -n $NAMESPACE --ignore-not-found
    kubectl delete pvc -l app=mongodb -n $NAMESPACE --ignore-not-found
    
    debug "Deleting External Secrets..."
    kubectl delete externalsecret mongodb-credentials -n $NAMESPACE --ignore-not-found
    kubectl delete secretstore vault-backend -n $NAMESPACE --ignore-not-found
    kubectl delete secret mongodb-credentials -n $NAMESPACE --ignore-not-found
    kubectl delete secret vault-token -n $NAMESPACE --ignore-not-found
    
    debug "Deleting namespace..."
    kubectl delete namespace $NAMESPACE --ignore-not-found
    
    success "MongoDB cleanup completed"
}

# Main function
main() {
    echo "MongoDB Deployment Script"
    echo "========================="
    debug "Script version: $SCRIPT_VERSION"
    debug "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    
    # Parse command line arguments
    if [ $# -eq 0 ]; then
        show_help
        exit 1
    fi
    
    case "$1" in
        --deploy-mongodb)
            check_prerequisites
            create_namespace
            generate_credentials
            store_credentials_in_vault
            setup_external_secrets
            deploy_mongodb
            setup_port_forward
            ;;
        --check-health)
            check_health
            ;;
        --port-forward)
            setup_port_forward
            ;;
        --open-ui)
            open_mongo_express_ui
            ;;
        --test-connection)
            test_mongodb_connection
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
