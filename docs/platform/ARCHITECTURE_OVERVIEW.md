# Nexus Platform Architecture Overview

## 🎯 **Platform Vision**

Nexus Platform is a **multi-tenant, microservices-based platform** that provides:

- **Unified Authentication**: Single sign-on across all services
- **Dynamic Access Control**: Database-driven service permissions
- **Scalable Architecture**: Independent service scaling
- **Security-First**: API Gateway with IP restrictions and rate limiting
- **Client Onboarding**: Automated client service provisioning

## 🏗️ **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Clients                             │
│  (Web Apps, Mobile Apps, Third-party Integrations)             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway                                  │
│  • Single Entry Point (Port 8080)                              │
│  • JWT Validation                                               │
│  • IP Restrictions                                              │
│  • Rate Limiting                                                │
│  • CORS Management                                              │
│  • Request Routing                                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Auth      │ │   Access    │ │   Other     │
│   Service   │ │   Control   │ │   Services  │
│             │ │   Service   │ │             │
│ • Keycloak  │ │ • Group     │ │ • Admin     │
│ • JWT       │ │   Mappings  │ │   Dashboard │
│ • OIDC      │ │ • Service   │ │ • ID        │
│             │ │   Access    │ │   Service   │
│             │ │ • Database  │ │ • Parking   │
│             │ │   Driven    │ │   Service   │
└─────────────┘ └─────────────┘ └─────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Shared Infrastructure                        │
│  • Database (PostgreSQL/MySQL)                                 │
│  • Monitoring (Prometheus, Grafana)                            │
│  • Logging (Loki)                                              │
│  • Kubernetes Cluster                                          │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 **Service Architecture**

### **1. API Gateway Service**
- **Port**: 8080 (External)
- **Purpose**: Single entry point for all external clients
- **Features**: Authentication, routing, security, monitoring
- **Technology**: Python HTTP Server (can be upgraded to Nginx/Envoy)

### **2. Authentication Service (Keycloak)**
- **Port**: 8080 (Internal)
- **Purpose**: Identity and access management
- **Features**: OIDC, JWT, user management, group management
- **Technology**: Keycloak (can be replaced with Auth0, Okta, etc.)

### **3. Access Control Service**
- **Port**: 8083 (Internal)
- **Purpose**: Database-driven service-to-group mappings
- **Features**: Dynamic access control, service management
- **Technology**: Python + SQLite (can be upgraded to PostgreSQL)

### **4. Admin Dashboard Service**
- **Port**: 8081 (Internal)
- **Purpose**: Platform administration and monitoring
- **Features**: Service management, monitoring, logs
- **Technology**: FastAPI + React

### **5. Landing Page Service**
- **Port**: 8082 (Internal)
- **Purpose**: User portal and service access
- **Features**: Service tiles, user dashboard
- **Technology**: HTML/CSS/JavaScript

## 🔒 **Security Architecture**

### **Multi-Layer Security**

1. **API Gateway Layer**
   - IP restrictions
   - Rate limiting
   - CORS management
   - Request validation

2. **Authentication Layer**
   - JWT validation
   - Token refresh
   - Session management
   - Multi-factor authentication

3. **Authorization Layer**
   - Group-based access control
   - Service-level permissions
   - Role-based access control
   - Audit logging

4. **Network Layer**
   - Internal service isolation
   - VPN access for admin
   - Firewall rules
   - SSL/TLS encryption

### **Security Benefits**

- **No Direct External Access**: Internal services not exposed
- **Single Point of Control**: All traffic through API Gateway
- **Flexible Authentication**: Can replace Keycloak without affecting other services
- **Audit Trail**: Complete request logging and monitoring

## 📊 **Multi-Tenant Architecture**

### **Tenant Isolation**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client A      │    │   Client B      │    │   Client C      │
│                 │    │                 │    │                 │
│ • Group: A      │    │ • Group: B      │    │ • Group: C      │
│ • Services:     │    │ • Services:     │    │ • Services:     │
│   - ID Service  │    │   - Parking     │    │   - All         │
│   - Analytics   │    │   - Reports     │    │   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   Access Control        │
                    │   Service               │
                    │                         │
                    │ • Database Mappings     │
                    │ • Group Validation      │
                    │ • Service Access        │
                    └─────────────────────────┘
```

### **Tenant Management**

- **Group-Based Isolation**: Each client has dedicated groups
- **Service Mapping**: Database-driven service access
- **Resource Quotas**: Per-tenant resource limits
- **Billing Integration**: Usage tracking and billing

## 🔄 **Data Flow**

### **1. User Authentication Flow**
```
1. User → API Gateway → Keycloak
2. Keycloak → User (JWT Token)
3. User → API Gateway (with JWT)
4. API Gateway → Access Control Service
5. Access Control Service → Database
6. Access Control Service → User (Service List)
```

### **2. Service Access Flow**
```
1. User → API Gateway → Target Service
2. API Gateway → Keycloak (Validate JWT)
3. API Gateway → Access Control (Check Permissions)
4. API Gateway → Target Service (if authorized)
5. Target Service → User (Response)
```

### **3. Admin Management Flow**
```
1. Admin → API Gateway → Admin Dashboard
2. Admin Dashboard → Access Control Service
3. Access Control Service → Database
4. Database → Access Control Service
5. Access Control Service → Admin Dashboard
6. Admin Dashboard → Admin (Management Interface)
```

## 🚀 **Deployment Architecture**

### **Development Environment**
- **Local Services**: Each service runs on localhost
- **SQLite Database**: Lightweight development database
- **No Load Balancing**: Direct service communication
- **Basic Security**: Development-friendly settings

### **Production Environment**
- **Kubernetes**: Container orchestration
- **PostgreSQL**: Production database
- **Load Balancer**: Traffic distribution
- **SSL/TLS**: Encrypted communication
- **Monitoring**: Prometheus, Grafana, Alertmanager

### **Scaling Strategy**
- **Horizontal Scaling**: Multiple service instances
- **Database Scaling**: Read replicas, connection pooling
- **Caching**: Redis for performance
- **CDN**: Static content delivery

## 📈 **Benefits of This Architecture**

### **For Platform Owners:**
- **Scalable**: Easy to add new services and clients
- **Maintainable**: Clear separation of concerns
- **Secure**: Multi-layer security approach
- **Flexible**: Can replace any component independently

### **For Clients:**
- **Unified Experience**: Single sign-on across services
- **Transparent**: Clear access control and permissions
- **Reliable**: High availability and monitoring
- **Customizable**: Per-client service configurations

### **For Developers:**
- **Modular**: Independent service development
- **Testable**: Isolated service testing
- **Deployable**: Independent service deployment
- **Documented**: Clear service boundaries and APIs

## 🔮 **Future Enhancements**

1. **Service Mesh**: Istio for advanced traffic management
2. **Event-Driven**: Kafka for service communication
3. **Machine Learning**: AI-powered access control
4. **Blockchain**: Decentralized identity management
5. **Edge Computing**: Global service distribution
