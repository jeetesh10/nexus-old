# Nexus Platform

A comprehensive microservices platform built with Kubernetes, featuring API Gateway, Service Mesh, Observability, and Database Orchestration.

## Quick Access (local/dev)

- Landing Page (public): http://localhost:8081/ (or http://localhost:$DASHBOARD_LOCAL_PORT/)
- Admin Dashboard (login required): http://localhost:8081/admin
- Keycloak (proxied via dashboard): http://localhost:8081/keycloak/
- Landing Page (public): http://localhost:8082/ (or http://localhost:$LANDING_LOCAL_PORT/)
- Admin Dashboard (login required): http://localhost:8083/admin
- Keycloak (proxied via dashboard): http://localhost:18081/keycloak/  # local admin UI forward: 18081 -> 8080
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100
- Alertmanager: http://localhost:9093

Codespaces note
- All browser links are relative (e.g., `/admin`, `/keycloak`) so they work behind Codespaces URLs like `https://<codespace>-8081.app.github.dev/`.
  If 8081 is occupied on your host, set DASHBOARD_LOCAL_PORT to a free port before running the start script.

See docs/platform/PORTS_MAP.md for the complete local port map and troubleshooting tips.
- Keycloak is proxied at `/keycloak` on the admin host, so no localhost is required.

## Current progress (short)

- Keycloak: deployment updated to read DB connection from a Kubernetes Secret (`keycloak-db-secret`) so Keycloak persists to PostgreSQL in-cluster.
- Seeding: a ConfigMap (`iac/kubernetes/keycloak-seed-configmap.yaml`) and Job (`iac/kubernetes/keycloak-seed-job.yaml`) were added to run the in-cluster seeder. Manual seeding via port-forward works; the Job has been iterated during debugging and can be re-run from the manifests.
- Ports: local developer port recommendations are centralized in `config/ports.yaml` and this README's port-forward examples follow those values.

Notes / next steps:
- To re-run the in-cluster seed job: `kubectl apply -f iac/kubernetes/keycloak-seed-configmap.yaml && kubectl apply -f iac/kubernetes/keycloak-seed-job.yaml` then monitor logs with `kubectl logs -f -l job-name=keycloak-seed-job`.
- If the Job fails, seed manually by port-forwarding Keycloak and running `./scripts/ops/seed-keycloak.sh` against the forwarded port.

## ✨ Recent Updates

- SmartCartBot service added (FastAPI, Python) and connected to Mongo Orchestrator via the Service DNS. With Linkerd, call the Orchestrator Service (port 80) instead of the Pod container port.
- Role-based access control (RBAC) integrated via Keycloak for:
  - Admin Dashboard (admin-only tabs and protected backend proxy routes)
  - Customer Portal (public landing + protected /private for group "customers")
- Keycloak seeding and group toggle scripts added under `scripts/ops/`.
- Ports centralized in `config/ports.yaml`; manifests aligned.

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
| **Auth API Service** | ⚠️ Review | — | Validate image in cluster |
| **Admin Dashboard** | 🟡 Configured | — | OIDC + guards added; redeploy/test |
| **Customer Portal** | 🟡 Configured | — | OIDC + protected route; redeploy/test |
| **SmartCartBot** | ✅ Working | 100% | Connected via Orchestrator Service DNS |
| **MongoDB Orchestrator** | ✅ Working | 100% | Use Service DNS through Linkerd |
| **PostgreSQL Orchestrator** | 🟡 Review | — | Validate after image load |
| **Keycloak** | 🟡 Setup Ready | — | Seed scripts provided; deploy if missing |

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

# Admin Dashboard
kubectl port-forward service/admin-dashboard-service 8000:8000

# Customer Portal
kubectl port-forward service/customer-portal 8002:8002

# Keycloak (if deployed as keycloak-service)
# Recommended local admin UI port-forward (matches developer convention in `config/ports.yaml` comments)
kubectl port-forward service/keycloak-service 18081:8080
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
kind load docker-image --name nexus nexus/auth-api:latest
kind load docker-image --name nexus nexus/admin-dashboard:latest
kind load docker-image --name nexus nexus/mongodb-orchestrator:latest
kind load docker-image --name nexus nexus/postgresql-orchestrator:latest

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

## 🔐 Auth & RBAC Setup (Keycloak)

This repository includes a simple, group-based RBAC flow using Keycloak. Admins belong to group `platform-admins`; customers belong to group `customers`. Tokens carry a `groups` claim.

### 1) Seed realm, clients, groups, and users

Use the helper script to create realm `nexus`, public clients `admin-dashboard` and `customer-portal`, groups, and demo users.

```bash
./scripts/ops/seed-keycloak.sh
```

What it creates
- Realm: `nexus`
- Clients: `admin-dashboard` (public), `customer-portal` (public)
- Groups: `platform-admins`, `customers`
- Users: `alice-admin` (admin), `bob-customer` (customer)
- Mapper: `groups` claim included in tokens

Notes
- If Keycloak isn’t deployed in-cluster, you can point the script to an external Keycloak by setting environment variables as instructed in the script header.
- If you need an in-cluster Keycloak, consider a Helm chart (Bitnami or Codecentric) and expose it as `keycloak-service` on 8080 to match defaults here.

### 2) Validate Admin Dashboard

Port-forward and open http://localhost:8000

```bash
kubectl port-forward service/admin-dashboard-service 8000:8000
```

Expected behavior
- You’ll be redirected to Keycloak to sign in.
- Sign in as `alice-admin`.
- Admin-only tabs appear; backend routes guarded by JWT + `platform-admins` group.

### 3) Validate Customer Portal

Port-forward and open http://localhost:8002

```bash
kubectl port-forward service/customer-portal 8002:8002
```

Expected behavior
- Public landing page is accessible without login.
- Clicking login uses Keycloak; sign in as `bob-customer`.
- Access to `/private` requires membership in `customers`.

### 4) Toggle group membership live

Use the helper to add/remove a user from a group and observe access changes after a refresh or new login.

```bash
# Add bob-customer to platform-admins (grant admin access)
./scripts/ops/keycloak-toggle-group.sh add bob-customer platform-admins

# Remove bob-customer from platform-admins
./scripts/ops/keycloak-toggle-group.sh remove bob-customer platform-admins
```

Troubleshooting
- If tokens don’t include the `groups` claim, re-run the seed script to ensure the mapper exists.
- Ensure the apps have these env vars (see k8s manifests): `KEYCLOAK_URL`, `KEYCLOAK_REALM`, `ADMIN_CLIENT_ID`/`CUSTOMER_CLIENT_ID`, and required group names.
- Frontend uses keycloak-js; backend verifies JWT via JWKS (python-jose).

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
- **Authentication**: Keycloak-based RBAC integrated (seed + manifests provided)

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
- **Authentication**: 🟡 Config staged (deploy Keycloak or configure external)

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

**Last Updated**: October 28, 2025  
**Status**: � Fixes in progress — Keycloak persistence & seeding being finalized  
**Next Update**: After in-cluster seed job completes and Keycloak persistence is validated

## SmartCartBot connectivity note

When running under Linkerd, do not call the MongoDB Orchestrator on its Pod container port (e.g., `:8080`). Always use the Service DNS without an explicit port (defaults to Service port 80), for example:

```
http://mongodb-orchestrator.default.svc.cluster.local
```

Otherwise, you may see Linkerd errors like “forbidden TCP route default.undefined-port”. Probes can continue to use the container’s port.

## Ports configuration (config/ports.yaml)

This repository centralizes container and service port values in `config/ports.yaml`. Use this file as the single source-of-truth for containerPort, servicePort and ingressHost values for all services.

Why
- Avoids port mismatches between Docker images and Kubernetes manifests.
- Makes it easy to review and change ports in one place before applying manifests or CI templating.

Location
- config/ports.yaml

How to use
1. Update `config/ports.yaml` with the service entry:
   - containerPort: the port your container listens on
   - servicePort: the ClusterIP/Service port
   - ingressHost: (optional) host for ingress testing

2. Keep manifests in sync:
   - Prefer templating (Helm, Kustomize, yq, or envsubst) to inject values from `config/ports.yaml` into manifests during CI/CD or local deploys.
   - If you need an immediate live fix, patch the deployment in-place to the port in `config/ports.yaml`.

Quick patch example (set mongodb-orchestrator containerPort and probes to 8080)
```bash
kubectl -n default patch deployment mongodb-orchestrator --type='merge' --patch '{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "mongodb-orchestrator",
            "ports": [{"containerPort": 8080}],
            "livenessProbe": {"httpGet": {"path": "/health", "port": 8080}},
            "readinessProbe": {"httpGet": {"path": "/health", "port": 8080}}
          }
        ]
      }
    }
  }
}'
kubectl -n default rollout status deployment/mongodb-orchestrator --timeout=300s
```

Recommended automation
- Use Helm values or Kustomize patches that read `config/ports.yaml` at build/deploy time.
- For simple scripts you can use `yq` to extract a port:
```bash
PORT=$(yq e '.services.mongodb-orchestrator.containerPort' config/ports.yaml)
# then use envsubst/templating to render manifests with $PORT
```

Debugging notes
- If pods show `CrashLoopBackOff` with Linkerd error "Connection refused", confirm the app is listening on the containerPort defined in `config/ports.yaml` and that the deployment’s liveness/readiness probes use the same port.
- Check container command and exposed ports:
```bash
docker inspect --format '{{json .Config.Cmd}} {{json .Config.ExposedPorts}}' <image>
kubectl -n default logs <pod> -c mongodb-orchestrator --tail=200
kubectl -n default describe pod <pod>
```

Addendum
- When adding a new service, add an entry to `config/ports.yaml` and update the corresponding k8s manifest (or template) to reference that value before applying.
- Prefer making `config/ports.yaml` the authoritative source in CI to avoid drift.
