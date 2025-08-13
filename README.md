# Nexus Platform

A comprehensive microservices platform built with Kubernetes, featuring API Gateway, Service Mesh, Observability, and Database Orchestration.

## 🚀 **Current Status**

**Production Readiness**: 75% Complete  
**Status**: 🔴 **CRITICAL ISSUES IDENTIFIED**  
**Estimated Time to Production**: 4-6 hours  

### 📊 **Component Status**

| Component | Status | Health | Notes |
|-----------|--------|--------|-------|
| **Kubernetes Infrastructure** | ✅ Working | 100% | Kind cluster operational |
| **NGINX Ingress Controller** | ✅ Working | 100% | Load balancing active |
| **APISIX API Gateway** | ✅ Working | 100% | Gateway with dashboard |
| **Linkerd Service Mesh** | ✅ Working | 100% | Control plane running |
| **MongoDB Database** | ✅ Working | 100% | Database instance running |
| **PostgreSQL Database** | ✅ Working | 100% | Database instance running |
| **Prometheus Monitoring** | ✅ Working | 100% | Metrics collection |
| **Grafana Dashboards** | ✅ Working | 100% | Visualization platform |
| **Alertmanager** | ✅ Working | 100% | Alert routing |
| **Loki Logging** | ✅ Working | 100% | Log aggregation |
| **Auth API Service** | ⚠️ Broken | 0% | Image loading issue |
| **Admin Dashboard** | ⚠️ Broken | 0% | Image loading issue |
| **MongoDB Orchestrator** | ⚠️ Broken | 0% | Image loading issue |
| **PostgreSQL Orchestrator** | ⚠️ Broken | 0% | Image loading issue |
| **Keycloak** | ❌ Missing | 0% | Not deployed |

## 🚨 **Critical Issues**

### **Issue 1: Image Loading Problems**
- **Problem**: Docker images not loading into kind cluster
- **Affected Services**: Auth API, Admin Dashboard, Database Orchestrators
- **Impact**: Application services cannot start
- **Priority**: 🔴 CRITICAL

### **Issue 2: Missing Authentication**
- **Problem**: Keycloak not deployed
- **Impact**: No authentication/authorization
- **Priority**: 🔴 CRITICAL

### **Issue 3: Service Mesh Integration**
- **Problem**: Services not injected with Linkerd sidecar
- **Impact**: No mTLS, no service mesh features
- **Priority**: 🟡 HIGH

## 📋 **Quick Start**

### **Prerequisites**
- Docker Desktop
- Kubernetes (kind)
- kubectl
- helm
- linkerd CLI

### **Installation**
```bash
# Clone the repository
git clone <repository-url>
cd Nexus

# Start the platform
./scripts/start-platform.sh

# Check status
./scripts/test-current-platform.sh
```

### **Access Services**
```bash
# APISIX Gateway
kubectl port-forward service/apisix-gateway 30080:80 -n apisix

# Grafana Dashboard
kubectl port-forward service/kube-prometheus-stack-grafana 3000:80 -n monitoring

# Prometheus
kubectl port-forward service/kube-prometheus-stack-prometheus 9090:9090 -n monitoring

# MongoDB
kubectl port-forward service/mongodb-service 27017:27017

# PostgreSQL
kubectl port-forward service/postgresql-service 5432:5432
```

## 🏗️ **Architecture**

### **System Architecture**
![System Architecture](docs/diagrams/system-architecture.md)

### **Request Flow**
![Request Flow](docs/diagrams/sequence-flow.md)

### **Troubleshooting Process**
![Troubleshooting Flow](docs/diagrams/troubleshooting-flowchart.md)

## 🔧 **Fix Process**

### **Step 1: Fix Image Loading (30 minutes)**
```bash
# Load images into kind cluster
kind load docker-image --name nexus-dev nexus/auth-api:latest
kind load docker-image --name nexus-dev nexus/admin-dashboard:latest
kind load docker-image --name nexus-dev nexus/mongodb-orchestrator:latest
kind load docker-image --name nexus-dev nexus/postgresql-orchestrator:latest

# Restart deployments
kubectl delete pods -l app=auth-api-service
kubectl delete pods -l app=admin-dashboard
kubectl delete pods -l app=mongodb-orchestrator
kubectl delete pods -l app=postgresql-orchestrator
```

### **Step 2: Deploy Keycloak (1 hour)**
```bash
# Deploy Keycloak
kubectl apply -f iac/kubernetes/keycloak-deployment.yaml

# Configure authentication
kubectl apply -f iac/kubernetes/keycloak-config.yaml
```

### **Step 3: Complete Integration (2 hours)**
```bash
# Run integration tests
./scripts/run-integration-tests.sh

# Run performance tests
k6 run scripts/k6-performance-test.js

# Run contract tests
npm test scripts/pact-contract-testing.js
```

## 🧪 **Testing**

### **Integration Tests**
```bash
./scripts/run-integration-tests.sh
```

### **Performance Tests**
```bash
k6 run scripts/k6-performance-test.js
```

### **Contract Tests**
```bash
npm test scripts/pact-contract-testing.js
```

### **Current Platform Tests**
```bash
./scripts/test-current-platform.sh
```

## 📁 **Project Structure**

```
Nexus/
├── docs/                          # Documentation
│   ├── diagrams/                  # System diagrams
│   │   ├── system-architecture.md
│   │   ├── sequence-flow.md
│   │   └── troubleshooting-flowchart.md
│   ├── platform/                  # Platform documentation
│   └── services/                  # Service documentation
├── iac/                          # Infrastructure as Code
│   └── kubernetes/               # Kubernetes manifests
├── scripts/                      # Automation scripts
├── services/                     # Microservices
│   ├── auth/                     # Authentication services
│   ├── database/                 # Database services
│   ├── admin-dashboard-service/  # Admin interface
│   └── api-gateway/             # API Gateway
├── postman-collections/          # API testing
└── README.md                     # This file
```

## 🔐 **Security**

- **Network Policies**: Implemented for service isolation
- **RBAC**: Basic Kubernetes RBAC configured
- **mTLS**: Linkerd service mesh encryption
- **Authentication**: Keycloak integration (pending)

## 📊 **Monitoring**

- **Prometheus**: Metrics collection
- **Grafana**: Dashboard visualization
- **Alertmanager**: Alert routing
- **Loki**: Log aggregation

## 🚀 **Production Deployment**

### **Current Readiness**
- **Infrastructure**: ✅ Ready
- **API Gateway**: ✅ Ready
- **Service Mesh**: ✅ Ready
- **Observability**: ✅ Ready
- **Databases**: ✅ Ready
- **Application Services**: ⚠️ Needs fixes
- **Authentication**: ❌ Missing

### **Deployment Checklist**
- [ ] Fix image loading issues
- [ ] Deploy Keycloak
- [ ] Complete service mesh integration
- [ ] Run integration tests
- [ ] Run performance tests
- [ ] Run security tests
- [ ] Validate all services
- [ ] Deploy to production

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📝 **Documentation**

- [Production Readiness Assessment](docs/PRODUCTION_READINESS_FINAL_ASSESSMENT.md)
- [Current Platform Test Report](current-platform-test-report.md)
- [API Documentation](docs/platform/API_DOCUMENTATION_STANDARDS.md)
- [Architecture Overview](docs/platform/ARCHITECTURE_OVERVIEW.md)

## 📞 **Support**

For issues and questions:
1. Check the troubleshooting flowchart
2. Review the current status documentation
3. Run the test scripts to identify issues
4. Create an issue with detailed information

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Last Updated**: August 13, 2025  
**Status**: 🔴 Critical Issues - Fix in Progress  
**Next Update**: After image loading fixes
