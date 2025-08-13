#!/bin/bash

# APISIX + Linkerd Deployment Script for Nexus Platform
# This script deploys APISIX and Linkerd for production use

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="nexus-platform"
MONITORING_NAMESPACE="monitoring"
APISIX_VERSION="3.0.0"
LINKERD_VERSION="2.12.0"

echo -e "${BLUE}🚀 Starting APISIX + Linkerd Deployment for Nexus Platform${NC}"

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl is not installed${NC}"
        exit 1
    fi
    
    # Check Helm
    if ! command -v helm &> /dev/null; then
        echo -e "${RED}❌ Helm is not installed${NC}"
        exit 1
    fi
    
    # Check Kubernetes cluster
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
        exit 1
    fi
    
    # Check cluster version
    K8S_VERSION=$(kubectl version --short --client | cut -d' ' -f3 | cut -d'.' -f2)
    if [ "$K8S_VERSION" -lt "24" ]; then
        echo -e "${RED}❌ Kubernetes version 1.24+ required${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to create namespaces
create_namespaces() {
    echo -e "${BLUE}📁 Creating namespaces...${NC}"
    
    # Create monitoring namespace
    kubectl create namespace $MONITORING_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Create nexus-platform namespace
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    echo -e "${GREEN}✅ Namespaces created${NC}"
}

# Function to deploy monitoring stack
deploy_monitoring() {
    echo -e "${BLUE}📊 Deploying monitoring stack...${NC}"
    
    # Add Prometheus Helm repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # Deploy Prometheus
    helm install prometheus prometheus-community/kube-prometheus-stack \
        --namespace $MONITORING_NAMESPACE \
        --create-namespace \
        --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi \
        --set grafana.enabled=true \
        --set grafana.adminPassword=admin123 \
        --wait
    
    # Add Jaeger Helm repository
    helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
    helm repo update
    
    # Deploy Jaeger
    helm install jaeger jaegertracing/jaeger \
        --namespace $MONITORING_NAMESPACE \
        --set storage.type=memory \
        --set ingress.enabled=false \
        --wait
    
    echo -e "${GREEN}✅ Monitoring stack deployed${NC}"
}

# Function to deploy APISIX
deploy_apisix() {
    echo -e "${BLUE}🚪 Deploying Apache APISIX...${NC}"
    
    # Add APISIX Helm repository
    helm repo add apisix https://charts.apiseven.com
    helm repo update
    
    # Create APISIX values file
    cat > apisix-values.yaml << EOF
apisix:
  replicaCount: 3
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 2000m
      memory: 4Gi
  
  etcd:
    replicaCount: 3
    persistence:
      enabled: true
      size: 20Gi
  
  gateway:
    type: LoadBalancer
    annotations:
      service.beta.kubernetes.io/aws-load-balancer-type: nlb
  
  admin:
    enabled: true
    type: ClusterIP
  
  dashboard:
    enabled: true
    service:
      type: ClusterIP

apisix-ingress-controller:
  enabled: true
  replicaCount: 2
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 200m
      memory: 256Mi
EOF
    
    # Deploy APISIX
    helm install apisix apisix/apisix \
        --namespace $NAMESPACE \
        --values apisix-values.yaml \
        --wait
    
    echo -e "${GREEN}✅ APISIX deployed${NC}"
}

# Function to deploy Linkerd
deploy_linkerd() {
    echo -e "${BLUE}🕸️ Deploying Linkerd Service Mesh...${NC}"
    
    # Install Linkerd CLI
    if ! command -v linkerd &> /dev/null; then
        echo -e "${YELLOW}📥 Installing Linkerd CLI...${NC}"
        curl -sL https://run.linkerd.io/install | sh
        export PATH=$PATH:$HOME/.linkerd2/bin
    fi
    
    # Install Linkerd control plane
    echo -e "${YELLOW}📦 Installing Linkerd control plane...${NC}"
    linkerd install --crds | kubectl apply -f -
    linkerd install | kubectl apply -f -
    
    # Wait for Linkerd to be ready
    echo -e "${YELLOW}⏳ Waiting for Linkerd to be ready...${NC}"
    kubectl wait --for=condition=ready pod -l app=linkerd-destination -n linkerd --timeout=300s
    kubectl wait --for=condition=ready pod -l app=linkerd-identity -n linkerd --timeout=300s
    kubectl wait --for=condition=ready pod -l app=linkerd-proxy-injector -n linkerd --timeout=300s
    
    # Install Linkerd dashboard
    echo -e "${YELLOW}📊 Installing Linkerd dashboard...${NC}"
    linkerd viz install | kubectl apply -f -
    
    # Verify installation
    echo -e "${YELLOW}🔍 Verifying Linkerd installation...${NC}"
    linkerd check
    
    echo -e "${GREEN}✅ Linkerd deployed${NC}"
}

# Function to configure APISIX routes
configure_apisix_routes() {
    echo -e "${BLUE}🔧 Configuring APISIX routes...${NC}"
    
    # Wait for APISIX to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=apisix -n $NAMESPACE --timeout=300s
    
    # Create APISIX routes
    cat > apisix-routes.yaml << EOF
apiVersion: apisix.apache.org/v2
kind: ApisixRoute
metadata:
  name: auth-route
  namespace: $NAMESPACE
spec:
  http:
    - name: auth-api
      match:
        hosts:
          - api.nexus.platform
        paths:
          - /api/auth/*
      backends:
        - serviceName: auth-api-service
          servicePort: 8084
      plugins:
        prometheus:
          prefer_name: true
        cors:
          allow_origins: "*"
          allow_methods: "GET,POST,PUT,DELETE,OPTIONS"
          allow_headers: "Content-Type,Authorization"
        rate-limiting:
          policy: local
          rate: 1000
          burst: 2000
          rejected_code: 429

---
apiVersion: apisix.apache.org/v2
kind: ApisixRoute
metadata:
  name: access-control-route
  namespace: $NAMESPACE
spec:
  http:
    - name: access-control-api
      match:
        hosts:
          - api.nexus.platform
        paths:
          - /api/services
          - /api/user-access
      backends:
        - serviceName: access-control-service
          servicePort: 8083
      plugins:
        prometheus:
          prefer_name: true
        cors:
          allow_origins: "*"
          allow_methods: "GET,POST,OPTIONS"
          allow_headers: "Content-Type,Authorization"
        rate-limiting:
          policy: local
          rate: 500
          burst: 1000
          rejected_code: 429

---
apiVersion: apisix.apache.org/v2
kind: ApisixRoute
metadata:
  name: admin-dashboard-route
  namespace: $NAMESPACE
spec:
  http:
    - name: admin-dashboard
      match:
        hosts:
          - admin.nexus.platform
        paths:
          - /admin/*
      backends:
        - serviceName: admin-dashboard-service
          servicePort: 8081
      plugins:
        prometheus:
          prefer_name: true
        cors:
          allow_origins: "*"
          allow_methods: "GET,POST,PUT,DELETE,OPTIONS"
          allow_headers: "Content-Type,Authorization"
        rate-limiting:
          policy: local
          rate: 100
          burst: 200
          rejected_code: 429

---
apiVersion: apisix.apache.org/v2
kind: ApisixRoute
metadata:
  name: landing-page-route
  namespace: $NAMESPACE
spec:
  http:
    - name: landing-page
      match:
        hosts:
          - platform.nexus.com
        paths:
          - /
          - /login.html
          - /landing-page.html
      backends:
        - serviceName: landing-page-service
          servicePort: 8082
      plugins:
        prometheus:
          prefer_name: true
        cors:
          allow_origins: "*"
          allow_methods: "GET,POST,OPTIONS"
          allow_headers: "Content-Type,Authorization"
EOF
    
    # Apply routes
    kubectl apply -f apisix-routes.yaml
    
    echo -e "${GREEN}✅ APISIX routes configured${NC}"
}

# Function to configure Linkerd policies
configure_linkerd_policies() {
    echo -e "${BLUE}🔧 Configuring Linkerd policies...${NC}"
    
    # Create service mesh policies
    cat > linkerd-policies.yaml << EOF
apiVersion: policy.linkerd.io/v1beta3
kind: Server
metadata:
  name: auth-api-server
  namespace: $NAMESPACE
spec:
  podSelector:
    matchLabels:
      app: auth-api-service
  port: 8084
  proxyProtocol: HTTP/1

---
apiVersion: policy.linkerd.io/v1beta3
kind: Server
metadata:
  name: access-control-server
  namespace: $NAMESPACE
spec:
  podSelector:
    matchLabels:
      app: access-control-service
  port: 8083
  proxyProtocol: HTTP/1

---
apiVersion: policy.linkerd.io/v1beta3
kind: Server
metadata:
  name: admin-dashboard-server
  namespace: $NAMESPACE
spec:
  podSelector:
    matchLabels:
      app: admin-dashboard-service
  port: 8081
  proxyProtocol: HTTP/1

---
apiVersion: policy.linkerd.io/v1beta3
kind: Server
metadata:
  name: landing-page-server
  namespace: $NAMESPACE
spec:
  podSelector:
    matchLabels:
      app: landing-page-service
  port: 8082
  proxyProtocol: HTTP/1
EOF
    
    # Apply policies
    kubectl apply -f linkerd-policies.yaml
    
    echo -e "${GREEN}✅ Linkerd policies configured${NC}"
}

# Function to configure monitoring
configure_monitoring() {
    echo -e "${BLUE}📊 Configuring monitoring...${NC}"
    
    # Create Prometheus configuration
    cat > prometheus-config.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: $MONITORING_NAMESPACE
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
      - job_name: 'apisix'
        static_configs:
          - targets: ['apisix-admin.$NAMESPACE.svc.cluster.local:9180']
        metrics_path: /apisix/prometheus/metrics
      
      - job_name: 'linkerd'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            action: replace
            target_label: __metrics_path__
            regex: (.+)
      
      - job_name: 'nexus-services'
        static_configs:
          - targets: 
              - 'auth-api-service.$NAMESPACE.svc.cluster.local:8084'
              - 'access-control-service.$NAMESPACE.svc.cluster.local:8083'
              - 'admin-dashboard-service.$NAMESPACE.svc.cluster.local:8081'
        metrics_path: /health
EOF
    
    # Apply monitoring configuration
    kubectl apply -f prometheus-config.yaml
    
    # Create Grafana dashboards
    cat > grafana-dashboards.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: $MONITORING_NAMESPACE
data:
  apisix-dashboard.json: |
    {
      "dashboard": {
        "title": "APISIX Dashboard",
        "panels": [
          {
            "title": "Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(apisix_http_requests_total[5m])",
                "legendFormat": "{{route}}"
              }
            ]
          },
          {
            "title": "Response Time",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(apisix_http_latency_bucket[5m]))",
                "legendFormat": "95th percentile"
              }
            ]
          }
        ]
      }
    }
  
  linkerd-dashboard.json: |
    {
      "dashboard": {
        "title": "Linkerd Service Mesh",
        "panels": [
          {
            "title": "Service Success Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(linkerd_proxy_request_total{response_class!=\"failure\"}[5m]) / rate(linkerd_proxy_request_total[5m])",
                "legendFormat": "{{dst}}"
              }
            ]
          }
        ]
      }
    }
EOF
    
    # Apply Grafana dashboards
    kubectl apply -f grafana-dashboards.yaml
    
    echo -e "${GREEN}✅ Monitoring configured${NC}"
}

# Function to configure security
configure_security() {
    echo -e "${BLUE}🔒 Configuring security...${NC}"
    
    # Create network policies
    cat > network-policies.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: apisix-network-policy
  namespace: $NAMESPACE
spec:
  podSelector:
    matchLabels:
      app: apisix
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 80
        - protocol: TCP
          port: 443
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: $NAMESPACE
      ports:
        - protocol: TCP
          port: 8080
        - protocol: TCP
          port: 8081
        - protocol: TCP
          port: 8083
        - protocol: TCP
          port: 8084

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: service-network-policy
  namespace: $NAMESPACE
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: $NAMESPACE
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: $NAMESPACE
EOF
    
    # Apply network policies
    kubectl apply -f network-policies.yaml
    
    # Create RBAC
    cat > rbac-config.yaml << EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: apisix-admin
rules:
  - apiGroups: ["apisix.apache.org"]
    resources: ["routes", "services", "upstreams"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: apisix-admin-binding
subjects:
  - kind: ServiceAccount
    name: apisix-admin
    namespace: $NAMESPACE
roleRef:
  kind: ClusterRole
  name: apisix-admin
  apiGroup: rbac.authorization.k8s.io
EOF
    
    # Apply RBAC
    kubectl apply -f rbac-config.yaml
    
    echo -e "${GREEN}✅ Security configured${NC}"
}

# Function to verify deployment
verify_deployment() {
    echo -e "${BLUE}🔍 Verifying deployment...${NC}"
    
    # Check APISIX
    echo -e "${YELLOW}📊 Checking APISIX...${NC}"
    kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=apisix
    
    # Check Linkerd
    echo -e "${YELLOW}📊 Checking Linkerd...${NC}"
    linkerd check
    
    # Check monitoring
    echo -e "${YELLOW}📊 Checking monitoring...${NC}"
    kubectl get pods -n $MONITORING_NAMESPACE
    
    # Get service URLs
    echo -e "${YELLOW}🌐 Service URLs:${NC}"
    APISIX_IP=$(kubectl get svc -n $NAMESPACE apisix-gateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -n "$APISIX_IP" ]; then
        echo -e "${GREEN}APISIX Gateway: http://$APISIX_IP${NC}"
    else
        echo -e "${YELLOW}APISIX Gateway: LoadBalancer IP not yet assigned${NC}"
    fi
    
    echo -e "${GREEN}✅ Deployment verification completed${NC}"
}

# Function to display next steps
display_next_steps() {
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo -e "${YELLOW}1. Configure Keycloak integration in APISIX${NC}"
    echo -e "${YELLOW}2. Inject Linkerd sidecars into existing services${NC}"
    echo -e "${YELLOW}3. Test authentication and authorization${NC}"
    echo -e "${YELLOW}4. Configure monitoring dashboards${NC}"
    echo -e "${YELLOW}5. Set up alerting rules${NC}"
    echo -e "${YELLOW}6. Perform load testing${NC}"
    echo -e "${YELLOW}7. Document operational procedures${NC}"
}

# Main execution
main() {
    check_prerequisites
    create_namespaces
    deploy_monitoring
    deploy_apisix
    deploy_linkerd
    configure_apisix_routes
    configure_linkerd_policies
    configure_monitoring
    configure_security
    verify_deployment
    display_next_steps
    
    echo -e "${GREEN}🎉 APISIX + Linkerd deployment completed successfully!${NC}"
}

# Run main function
main "$@"
