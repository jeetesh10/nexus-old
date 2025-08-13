# Nexus Platform - System Architecture Diagram

## 🏗️ **Current System Architecture**

```mermaid
graph TB
    %% External Users
    subgraph "External Users"
        Client[Client Applications]
        Admin[Admin Users]
    end

    %% Load Balancer / Ingress
    subgraph "Load Balancer Layer"
        LB[Load Balancer]
        NGINX[NGINX Ingress Controller<br/>✅ Running<br/>Port: 30398]
    end

    %% API Gateway Layer
    subgraph "API Gateway Layer"
        APISIX[APISIX API Gateway<br/>✅ Running<br/>Port: 31581]
        APISIX_DASH[APISIX Dashboard<br/>✅ Running<br/>Port: 30897]
        APISIX_ETCD[APISIX ETCD<br/>✅ Running]
    end

    %% Service Mesh Layer
    subgraph "Service Mesh Layer"
        LINKERD[Linkerd Control Plane<br/>✅ Running]
        LINKERD_ID[Linkerd Identity<br/>✅ Running]
        LINKERD_DST[Linkerd Destination<br/>✅ Running]
    end

    %% Application Services Layer
    subgraph "Application Services Layer"
        AUTH_API[Auth API Service<br/>⚠️ Deployed but Broken<br/>Image Loading Issue]
        ADMIN_DASH[Admin Dashboard<br/>⚠️ Deployed but Broken<br/>Image Loading Issue]
        MONGODB_ORCH[MongoDB Orchestrator<br/>⚠️ Deployed but Broken<br/>Image Loading Issue]
        POSTGRES_ORCH[PostgreSQL Orchestrator<br/>⚠️ Deployed but Broken<br/>Image Loading Issue]
    end

    %% Database Layer
    subgraph "Database Layer"
        MONGODB[MongoDB Database<br/>✅ Running<br/>Port: 27017]
        POSTGRESQL[PostgreSQL Database<br/>✅ Running<br/>Port: 5432]
    end

    %% Authentication Layer
    subgraph "Authentication Layer"
        KEYCLOAK[Keycloak<br/>❌ Not Deployed<br/>Missing Authentication Provider]
    end

    %% Observability Layer
    subgraph "Observability Layer"
        PROMETHEUS[Prometheus<br/>✅ Running<br/>Port: 9090]
        GRAFANA[Grafana<br/>✅ Running<br/>Port: 3000]
        ALERTMANAGER[Alertmanager<br/>✅ Running<br/>Port: 9093]
        LOKI[Loki<br/>✅ Running<br/>Port: 3100]
    end

    %% Network Security
    subgraph "Security Layer"
        NETWORK_POL[Network Policies<br/>✅ Implemented]
        RBAC[RBAC<br/>✅ Basic Implementation]
    end

    %% Connections - Working
    Client --> LB
    Admin --> LB
    LB --> NGINX
    NGINX --> APISIX
    
    %% Service Mesh Connections
    APISIX -.->|mTLS| LINKERD
    AUTH_API -.->|mTLS| LINKERD
    ADMIN_DASH -.->|mTLS| LINKERD
    MONGODB_ORCH -.->|mTLS| LINKERD
    POSTGRES_ORCH -.->|mTLS| LINKERD

    %% Database Connections
    MONGODB_ORCH --> MONGODB
    POSTGRES_ORCH --> POSTGRESQL

    %% Authentication Connections
    AUTH_API -.->|❌ Missing| KEYCLOAK

    %% Monitoring Connections
    PROMETHEUS --> MONGODB
    PROMETHEUS --> POSTGRESQL
    PROMETHEUS --> AUTH_API
    PROMETHEUS --> ADMIN_DASH
    PROMETHEUS --> MONGODB_ORCH
    PROMETHEUS --> POSTGRES_ORCH

    %% Styling
    classDef working fill:#90EE90,stroke:#006400,stroke-width:2px
    classDef broken fill:#FFB6C1,stroke:#8B0000,stroke-width:2px
    classDef missing fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px
    classDef security fill:#87CEEB,stroke:#0000CD,stroke-width:2px

    class APISIX,APISIX_DASH,APISIX_ETCD,NGINX,LINKERD,LINKERD_ID,LINKERD_DST,MONGODB,POSTGRESQL,PROMETHEUS,GRAFANA,ALERTMANAGER,LOKI working
    class AUTH_API,ADMIN_DASH,MONGODB_ORCH,POSTGRES_ORCH broken
    class KEYCLOAK missing
    class NETWORK_POL,RBAC security
```

## 🔍 **Component Status Legend**

### ✅ **Working Components (Green)**
- **Infrastructure**: Kubernetes cluster, NGINX ingress
- **API Gateway**: APISIX with dashboard and ETCD
- **Service Mesh**: Linkerd control plane components
- **Databases**: MongoDB and PostgreSQL instances
- **Observability**: Prometheus, Grafana, Alertmanager, Loki
- **Security**: Network policies and RBAC

### ⚠️ **Broken Components (Red)**
- **Auth API Service**: Deployed but image loading failed
- **Admin Dashboard**: Deployed but image loading failed
- **MongoDB Orchestrator**: Deployed but image loading failed
- **PostgreSQL Orchestrator**: Deployed but image loading failed

### ❌ **Missing Components (Orange)**
- **Keycloak**: Authentication provider not deployed

## 🚨 **Critical Issues to Fix**

### **1. Image Loading Issues**
```
Problem: Docker images not loading into kind cluster
Services Affected: Auth API, Admin Dashboard, Database Orchestrators
Impact: Application services cannot start
Priority: 🔴 CRITICAL
```

### **2. Missing Authentication**
```
Problem: Keycloak not deployed
Services Affected: All application services
Impact: No authentication/authorization
Priority: 🔴 CRITICAL
```

### **3. Service Mesh Integration**
```
Problem: Services not injected with Linkerd sidecar
Services Affected: All application services
Impact: No mTLS, no service mesh features
Priority: 🟡 HIGH
```

## 📊 **Current Metrics**

- **Total Components**: 15
- **Working**: 11 (73%)
- **Broken**: 4 (27%)
- **Missing**: 1 (7%)
- **Production Readiness**: 75%

## 🎯 **Fix Priority Order**

1. **Fix Image Loading** (30 minutes)
2. **Deploy Keycloak** (1 hour)
3. **Restart Services** (15 minutes)
4. **Test Integration** (2 hours)
5. **Performance Testing** (1 hour)
