# Nexus Platform - Request Flow Sequence Diagram

## 🔄 **Current Request Flow (With Issues)**

```mermaid
sequenceDiagram
    participant Client
    participant LB as Load Balancer
    participant NGINX as NGINX Ingress
    participant APISIX as APISIX Gateway
    participant AUTH as Auth API Service
    participant KEYCLOAK as Keycloak
    participant MONGODB_ORCH as MongoDB Orchestrator
    participant MONGODB as MongoDB Database
    participant POSTGRES_ORCH as PostgreSQL Orchestrator
    participant POSTGRES as PostgreSQL Database
    participant ADMIN as Admin Dashboard
    participant PROM as Prometheus
    participant GRAFANA as Grafana

    %% Initial Request Flow
    Client->>LB: 1. HTTP Request
    LB->>NGINX: 2. Route to NGINX Ingress
    NGINX->>APISIX: 3. Forward to APISIX Gateway
    
    %% Authentication Flow (BROKEN)
    APISIX->>AUTH: 4. Route to Auth API
    Note over AUTH: ❌ BROKEN: Image Loading Issue
    AUTH-->>APISIX: 5. ❌ Service Unavailable
    APISIX-->>NGINX: 6. ❌ 503 Service Unavailable
    NGINX-->>LB: 7. ❌ Error Response
    LB-->>Client: 8. ❌ 503 Service Unavailable

    %% Alternative Flow - Direct Database Access (WORKING)
    Client->>LB: 9. Direct Database Request
    LB->>NGINX: 10. Route to Database
    NGINX->>MONGODB_ORCH: 11. Route to MongoDB Orchestrator
    Note over MONGODB_ORCH: ❌ BROKEN: Image Loading Issue
    MONGODB_ORCH-->>NGINX: 12. ❌ Service Unavailable
    
    %% Working Database Direct Access
    NGINX->>MONGODB: 13. Direct MongoDB Access
    Note over MONGODB: ✅ WORKING: Database Running
    MONGODB-->>NGINX: 14. ✅ Database Response
    NGINX-->>LB: 15. ✅ Success Response
    LB-->>Client: 16. ✅ Data Returned

    %% Admin Dashboard Flow (BROKEN)
    Client->>LB: 17. Admin Dashboard Request
    LB->>NGINX: 18. Route to Admin Dashboard
    NGINX->>ADMIN: 19. Route to Admin Dashboard
    Note over ADMIN: ❌ BROKEN: Image Loading Issue
    ADMIN-->>NGINX: 20. ❌ Service Unavailable
    NGINX-->>LB: 21. ❌ Error Response
    LB-->>Client: 22. ❌ 503 Service Unavailable

    %% Monitoring Flow (WORKING)
    Client->>LB: 23. Monitoring Request
    LB->>NGINX: 24. Route to Grafana
    NGINX->>GRAFANA: 25. Access Grafana Dashboard
    Note over GRAFANA: ✅ WORKING: Monitoring Running
    GRAFANA->>PROM: 26. Query Prometheus
    Note over PROM: ✅ WORKING: Metrics Collection
    PROM-->>GRAFANA: 27. ✅ Metrics Data
    GRAFANA-->>NGINX: 28. ✅ Dashboard Response
    NGINX-->>LB: 29. ✅ Success Response
    LB-->>Client: 30. ✅ Dashboard Displayed
```

## 🚨 **Current Issues in Flow**

### **Issue 1: Authentication Service Broken**
```
Step 4-8: Auth API Service
- Problem: Image loading failed
- Impact: No authentication possible
- Status: ❌ BROKEN
- Fix Required: Resolve image loading
```

### **Issue 2: Database Orchestrators Broken**
```
Step 11-12: MongoDB Orchestrator
Step 11-12: PostgreSQL Orchestrator
- Problem: Image loading failed
- Impact: No database orchestration
- Status: ❌ BROKEN
- Fix Required: Resolve image loading
```

### **Issue 3: Admin Dashboard Broken**
```
Step 19-22: Admin Dashboard
- Problem: Image loading failed
- Impact: No admin interface
- Status: ❌ BROKEN
- Fix Required: Resolve image loading
```

### **Issue 4: Missing Keycloak**
```
Step 4: Keycloak Integration
- Problem: Keycloak not deployed
- Impact: No authentication provider
- Status: ❌ MISSING
- Fix Required: Deploy Keycloak
```

## ✅ **Working Flows**

### **Flow 1: Direct Database Access**
```
Steps 13-16: Direct MongoDB/PostgreSQL
- Status: ✅ WORKING
- Access: Direct database connections
- Use Case: Database operations
```

### **Flow 2: Monitoring & Observability**
```
Steps 23-30: Grafana + Prometheus
- Status: ✅ WORKING
- Access: Metrics and dashboards
- Use Case: System monitoring
```

### **Flow 3: Infrastructure Components**
```
Steps 1-3: Load Balancer + NGINX + APISIX
- Status: ✅ WORKING
- Access: Gateway and routing
- Use Case: Request routing
```

## 🔧 **Fix Sequence**

### **Phase 1: Fix Image Loading (30 minutes)**
```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Docker as Docker
    participant Kind as Kind Cluster
    participant K8s as Kubernetes

    Dev->>Docker: 1. Verify images exist
    Docker-->>Dev: 2. ✅ Images confirmed
    Dev->>Kind: 3. Load images into cluster
    Kind-->>Dev: 4. ✅ Images loaded
    Dev->>K8s: 5. Restart deployments
    K8s-->>Dev: 6. ✅ Services running
```

### **Phase 2: Deploy Keycloak (1 hour)**
```mermaid
sequenceDiagram
    participant Dev as Developer
    participant K8s as Kubernetes
    participant Keycloak as Keycloak
    participant Auth as Auth API

    Dev->>K8s: 1. Deploy Keycloak
    K8s->>Keycloak: 2. Start Keycloak
    Keycloak-->>K8s: 3. ✅ Keycloak running
    Dev->>Auth: 4. Configure Auth API
    Auth->>Keycloak: 5. Connect to Keycloak
    Keycloak-->>Auth: 6. ✅ Authentication ready
```

### **Phase 3: Complete Integration (2 hours)**
```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Test as Test Suite
    participant Platform as Nexus Platform

    Dev->>Test: 1. Run integration tests
    Test->>Platform: 2. Test all services
    Platform-->>Test: 3. ✅ All tests pass
    Dev->>Test: 4. Run performance tests
    Test->>Platform: 5. Load test platform
    Platform-->>Test: 6. ✅ Performance OK
    Dev->>Test: 7. Run security tests
    Test->>Platform: 8. Security validation
    Platform-->>Test: 9. ✅ Security OK
```

## 📊 **Current Success Rate**

- **Total Flows**: 6
- **Working Flows**: 3 (50%)
- **Broken Flows**: 3 (50%)
- **Critical Flows**: 2 (33% working)

## 🎯 **Expected Flow After Fixes**

```mermaid
sequenceDiagram
    participant Client
    participant LB as Load Balancer
    participant NGINX as NGINX Ingress
    participant APISIX as APISIX Gateway
    participant AUTH as Auth API Service
    participant KEYCLOAK as Keycloak
    participant MONGODB_ORCH as MongoDB Orchestrator
    participant MONGODB as MongoDB Database
    participant POSTGRES_ORCH as PostgreSQL Orchestrator
    participant POSTGRES as PostgreSQL Database
    participant ADMIN as Admin Dashboard

    %% Complete Working Flow
    Client->>LB: 1. HTTP Request
    LB->>NGINX: 2. Route to NGINX Ingress
    NGINX->>APISIX: 3. Forward to APISIX Gateway
    APISIX->>AUTH: 4. Route to Auth API
    AUTH->>KEYCLOAK: 5. Authenticate with Keycloak
    KEYCLOAK-->>AUTH: 6. ✅ JWT Token
    AUTH-->>APISIX: 7. ✅ Authenticated Response
    APISIX->>MONGODB_ORCH: 8. Route to MongoDB Orchestrator
    MONGODB_ORCH->>MONGODB: 9. Database Operation
    MONGODB-->>MONGODB_ORCH: 10. ✅ Data Response
    MONGODB_ORCH-->>APISIX: 11. ✅ Orchestrated Response
    APISIX-->>NGINX: 12. ✅ Success Response
    NGINX-->>LB: 13. ✅ Success Response
    LB-->>Client: 14. ✅ Complete Response
```
